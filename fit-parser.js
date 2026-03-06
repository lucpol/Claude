/**
 * Minimal FIT file parser for activity records.
 * Parses binary FIT files (Garmin/ANT+ standard) and extracts
 * per-second record data including HR, power, speed, cadence, altitude, temperature.
 */
const FitParser = (() => {

    const FIT_MESG_NUM = {
        FILE_ID: 0,
        SESSION: 18,
        LAP: 19,
        RECORD: 20,
        EVENT: 21,
        DEVICE_INFO: 23,
        ACTIVITY: 34,
    };

    const BASE_TYPES = {
        0x00: { name: 'enum', size: 1, invalid: 0xFF },
        0x01: { name: 'sint8', size: 1, invalid: 0x7F },
        0x02: { name: 'uint8', size: 1, invalid: 0xFF },
        0x83: { name: 'sint16', size: 2, invalid: 0x7FFF },
        0x84: { name: 'uint16', size: 2, invalid: 0xFFFF },
        0x85: { name: 'sint32', size: 4, invalid: 0x7FFFFFFF },
        0x86: { name: 'uint32', size: 4, invalid: 0xFFFFFFFF },
        0x07: { name: 'string', size: 1, invalid: 0x00 },
        0x88: { name: 'float32', size: 4, invalid: 0xFFFFFFFF },
        0x89: { name: 'float64', size: 8, invalid: null },
        0x0A: { name: 'uint8z', size: 1, invalid: 0x00 },
        0x8B: { name: 'uint16z', size: 2, invalid: 0x0000 },
        0x8C: { name: 'uint32z', size: 4, invalid: 0x00000000 },
        0x0D: { name: 'byte', size: 1, invalid: 0xFF },
        0x8E: { name: 'sint64', size: 8, invalid: null },
        0x8F: { name: 'uint64', size: 8, invalid: null },
        0x90: { name: 'uint64z', size: 8, invalid: null },
    };

    // Record message field definitions
    const RECORD_FIELDS = {
        253: 'timestamp',
        0: 'position_lat',
        1: 'position_long',
        2: 'altitude',
        3: 'heart_rate',
        4: 'cadence',
        5: 'distance',
        6: 'speed',
        7: 'power',
        13: 'temperature',
        73: 'enhanced_speed',
        78: 'enhanced_altitude',
    };

    function getBaseType(baseTypeNum) {
        return BASE_TYPES[baseTypeNum] || BASE_TYPES[0x00];
    }

    function readValue(view, offset, baseType, size, littleEndian) {
        const bt = baseType.name;
        if (offset + size > view.byteLength) return { value: null, bytesRead: size };

        let value = null;
        try {
            switch (bt) {
                case 'enum':
                case 'uint8':
                case 'uint8z':
                case 'byte':
                    value = view.getUint8(offset);
                    break;
                case 'sint8':
                    value = view.getInt8(offset);
                    break;
                case 'uint16':
                case 'uint16z':
                    value = view.getUint16(offset, littleEndian);
                    break;
                case 'sint16':
                    value = view.getInt16(offset, littleEndian);
                    break;
                case 'uint32':
                case 'uint32z':
                    value = view.getUint32(offset, littleEndian);
                    break;
                case 'sint32':
                    value = view.getInt32(offset, littleEndian);
                    break;
                case 'float32':
                    value = view.getFloat32(offset, littleEndian);
                    break;
                case 'float64':
                    value = view.getFloat64(offset, littleEndian);
                    break;
                case 'string': {
                    const bytes = [];
                    for (let i = 0; i < size; i++) {
                        const b = view.getUint8(offset + i);
                        if (b === 0) break;
                        bytes.push(b);
                    }
                    value = String.fromCharCode(...bytes);
                    break;
                }
                case 'sint64':
                case 'uint64':
                case 'uint64z':
                    // Read as two 32-bit values
                    value = view.getUint32(offset, littleEndian) +
                            view.getUint32(offset + 4, littleEndian) * 0x100000000;
                    break;
                default:
                    value = view.getUint8(offset);
            }
        } catch {
            value = null;
        }

        if (value !== null && baseType.invalid !== null && value === baseType.invalid) {
            value = null;
        }

        return { value, bytesRead: size };
    }

    function parse(arrayBuffer) {
        const view = new DataView(arrayBuffer);
        let offset = 0;

        // --- File Header ---
        const headerSize = view.getUint8(0);
        const protocolVersion = view.getUint8(1);
        const profileVersion = view.getUint16(2, true);
        const dataSize = view.getUint32(4, true);
        const dataType = String.fromCharCode(
            view.getUint8(8), view.getUint8(9), view.getUint8(10), view.getUint8(11)
        );

        if (dataType !== '.FIT') {
            throw new Error('Invalid FIT file: missing .FIT signature');
        }

        offset = headerSize;
        const dataEnd = headerSize + dataSize;

        // --- Parse messages ---
        const localMessageTypes = {};
        const records = [];
        const sessions = [];

        while (offset < dataEnd) {
            if (offset >= view.byteLength) break;

            const recordHeader = view.getUint8(offset);
            offset += 1;

            // Compressed timestamp header
            if (recordHeader & 0x80) {
                const localMsgType = (recordHeader >> 5) & 0x03;
                const def = localMessageTypes[localMsgType];
                if (!def) { continue; }
                // Skip data
                let totalSize = 0;
                for (const field of def.fields) totalSize += field.size;
                offset += totalSize;
                continue;
            }

            const isDefinition = (recordHeader & 0x40) !== 0;
            const localMsgType = recordHeader & 0x0F;
            const hasDeveloperData = (recordHeader & 0x20) !== 0;

            if (isDefinition) {
                // --- Definition message ---
                if (offset + 5 > view.byteLength) break;
                const reserved = view.getUint8(offset);
                const architecture = view.getUint8(offset + 1);
                const littleEndian = architecture === 0;
                const globalMsgNum = view.getUint16(offset + 2, littleEndian);
                const numFields = view.getUint8(offset + 4);
                offset += 5;

                const fields = [];
                for (let i = 0; i < numFields; i++) {
                    if (offset + 3 > view.byteLength) break;
                    const fieldDefNum = view.getUint8(offset);
                    const fieldSize = view.getUint8(offset + 1);
                    const baseTypeNum = view.getUint8(offset + 2);
                    offset += 3;
                    fields.push({
                        fieldDefNum,
                        size: fieldSize,
                        baseType: getBaseType(baseTypeNum & 0x9F),
                    });
                }

                let devFields = [];
                if (hasDeveloperData) {
                    if (offset < view.byteLength) {
                        const numDevFields = view.getUint8(offset);
                        offset += 1;
                        for (let i = 0; i < numDevFields; i++) {
                            if (offset + 3 > view.byteLength) break;
                            const devFieldNum = view.getUint8(offset);
                            const devFieldSize = view.getUint8(offset + 1);
                            const devIndex = view.getUint8(offset + 2);
                            offset += 3;
                            devFields.push({ size: devFieldSize });
                        }
                    }
                }

                localMessageTypes[localMsgType] = {
                    globalMsgNum,
                    littleEndian,
                    fields,
                    devFields,
                };
            } else {
                // --- Data message ---
                const def = localMessageTypes[localMsgType];
                if (!def) {
                    // Can't proceed without definition
                    break;
                }

                const values = {};
                for (const field of def.fields) {
                    const { value, bytesRead } = readValue(
                        view, offset, field.baseType, field.size, def.littleEndian
                    );
                    offset += field.size;

                    if (def.globalMsgNum === FIT_MESG_NUM.RECORD || def.globalMsgNum === FIT_MESG_NUM.SESSION) {
                        const fieldName = RECORD_FIELDS[field.fieldDefNum];
                        if (fieldName && value !== null) {
                            values[fieldName] = value;
                        }
                    }
                }

                // Skip developer fields
                if (def.devFields) {
                    for (const df of def.devFields) {
                        offset += df.size;
                    }
                }

                if (def.globalMsgNum === FIT_MESG_NUM.RECORD && Object.keys(values).length > 0) {
                    records.push(values);
                }
                if (def.globalMsgNum === FIT_MESG_NUM.SESSION) {
                    sessions.push(values);
                }
            }
        }

        return processRecords(records, sessions);
    }

    function processRecords(records, sessions) {
        // FIT epoch: Dec 31, 1989 00:00:00 UTC
        const FIT_EPOCH = 631065600;

        const processed = [];

        for (const rec of records) {
            const entry = {};

            if (rec.timestamp != null) {
                const unixTs = rec.timestamp + FIT_EPOCH;
                entry.timestamp = new Date(unixTs * 1000);
                entry.unix_ts = unixTs;
            } else {
                continue; // Skip records without timestamps
            }

            if (rec.heart_rate != null) entry.heart_rate = rec.heart_rate;
            if (rec.power != null) entry.power = rec.power;

            if (rec.enhanced_speed != null) {
                entry.speed = rec.enhanced_speed / 1000 * 3.6; // m/s*1000 -> km/h
            } else if (rec.speed != null) {
                entry.speed = rec.speed / 1000 * 3.6;
            }

            if (rec.cadence != null) entry.cadence = rec.cadence;

            if (rec.enhanced_altitude != null) {
                entry.altitude = (rec.enhanced_altitude / 5) - 500;
            } else if (rec.altitude != null) {
                entry.altitude = (rec.altitude / 5) - 500;
            }

            if (rec.temperature != null) entry.temperature = rec.temperature;

            processed.push(entry);
        }

        // Build summary from session data or calculate from records
        const summary = {};
        if (sessions.length > 0) {
            const s = sessions[0];
            if (s.heart_rate != null) summary.avg_heart_rate = s.heart_rate;
            if (s.power != null) summary.avg_power = s.power;
        }

        // Calculate summary from records
        const fields = ['heart_rate', 'power', 'speed', 'cadence', 'altitude', 'temperature'];
        for (const f of fields) {
            const vals = processed.filter(r => r[f] != null).map(r => r[f]);
            if (vals.length > 0) {
                summary[`avg_${f}`] = vals.reduce((a, b) => a + b, 0) / vals.length;
                summary[`max_${f}`] = Math.max(...vals);
                summary[`min_${f}`] = Math.min(...vals);
            }
        }

        if (processed.length > 0) {
            summary.start_time = processed[0].timestamp;
            summary.end_time = processed[processed.length - 1].timestamp;
            summary.duration_seconds = (processed[processed.length - 1].unix_ts - processed[0].unix_ts);
            summary.total_records = processed.length;
        }

        return { records: processed, summary };
    }

    return { parse };
})();
