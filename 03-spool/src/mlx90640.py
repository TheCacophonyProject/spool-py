"""
MLX90640 driver for MicroPython (Raspberry Pi Pico / RP2040).
Ports the official Melexis C library calibration pipeline.
"""
import math
import array

_SCALEALPHA = 0.000001

_STATUS_REG  = 0x8000
_CTRL_REG    = 0x800D
_EEPROM_ADDR = 0x2400
_PIXEL_ADDR  = 0x0400
_AUX_ADDR    = 0x0700


def _s8(v):
    return v - 256 if v > 127 else v

def _s16(v):
    return v - 65536 if v > 32767 else v

def _n1(v): return  v & 0x000F
def _n2(v): return (v >>  4) & 0x000F
def _n3(v): return (v >>  8) & 0x000F
def _n4(v): return (v >> 12) & 0x000F
def _msb(v): return (v >> 8) & 0xFF
def _lsb(v): return  v & 0xFF

def _mv_s16(mv, idx):
    """Signed 16-bit big-endian word from memoryview at word index idx."""
    b = idx << 1
    v = (mv[b] << 8) | mv[b + 1]
    return v - 65536 if v > 32767 else v


class MLX90640:
    def __init__(self, i2c, addr=0x33):
        self.i2c  = i2c
        self.addr = addr
        self.p    = None   # calibration params
        # Pre-allocated I/O buffers — avoids heap allocation on every frame.
        # Frame layout: 768 pixel words + 64 aux words = 1664 bytes.
        self._reg_buf = bytearray(2)
        self._sr_buf  = bytearray(2)
        self._fd_buf  = bytearray(1664)
        self._fd_mv   = memoryview(self._fd_buf)

    # ------------------------------------------------------------------ I2C --

    def _read(self, reg, n_words):
        """Read n_words uint16 values (used for EEPROM/setup; allocates lists)."""
        raw = self.i2c.readfrom_mem(self.addr, reg, n_words * 2, addrsize=16)
        return [(raw[i*2] << 8 | raw[i*2+1]) for i in range(n_words)]

    def _read_chunks(self, reg, n_words, chunk=128):
        """Chunked _read (used for EEPROM load only)."""
        out = []
        pos = 0
        while pos < n_words:
            sz = min(chunk, n_words - pos)
            out.extend(self._read(reg + pos, sz))
            pos += sz
        return out

    def _read_into(self, reg, mv):
        """Read directly into a memoryview slice — zero allocation."""
        self.i2c.readfrom_mem_into(self.addr, reg, mv, addrsize=16)

    def _read_chunks_into(self, reg, mv, chunk=128):
        """Chunked zero-allocation read into a memoryview."""
        pos = 0
        n_words = len(mv) >> 1
        while pos < n_words:
            n = min(chunk, n_words - pos)
            self._read_into(reg + pos, mv[pos << 1 : (pos + n) << 1])
            pos += n

    def _write(self, reg, val):
        self.i2c.writeto(self.addr, bytes([
            reg >> 8, reg & 0xFF, val >> 8, val & 0xFF
        ]))

    # --------------------------------------------------------- sensor setup --

    def set_refresh_rate(self, hz):
        codes = {1: 1, 2: 2, 4: 3, 8: 4, 16: 5, 32: 6, 64: 7}
        code = codes.get(hz, 3)
        reg = self._read(_CTRL_REG, 1)[0]
        self._write(_CTRL_REG, (reg & 0xFC7F) | (code << 7))

    def set_chess_mode(self):
        reg = self._read(_CTRL_REG, 1)[0]
        self._write(_CTRL_REG, reg | 0x1000)

    # ------------------------------------------------- calibration loading --

    def load_calibration(self):
        """Read EEPROM and extract all calibration parameters. Call once on startup."""
        ee = self._read_chunks(_EEPROM_ADDR, 832)
        p = {}
        _extract_vdd(ee, p)
        _extract_ptat(ee, p)
        _extract_gain(ee, p)
        _extract_tgc(ee, p)
        _extract_resolution(ee, p)
        _extract_ksta(ee, p)
        _extract_ksto(ee, p)
        _extract_cp(ee, p)       # must precede alpha
        _extract_cilc(ee, p)
        _extract_alpha(ee, p)
        _extract_offset(ee, p)
        _extract_kta(ee, p)
        _extract_kv(ee, p)
        self.p = p
        # Cache ctrl register mode bit — set_chess_mode/set_refresh_rate must be
        # called before load_calibration, or this will need updating.
        ctrl = self._read(_CTRL_REG, 1)[0]
        self._mode = (ctrl & 0x1000) >> 5   # 0 = interleaved, 128 = chess

    # ------------------------------------------------------- frame reading --

    def get_frame_data(self):
        """
        Poll until a new frame is ready, fill the internal buffer, and return it.
        Returns (memoryview of raw bytes, subpage 0-or-1).
        Buffer layout: bytes 0-1535 = 768 pixel words, 1536-1663 = 64 aux words,
        Word N lives at bytes N*2 : N*2+2.
        """
        sr = self._sr_buf
        while True:
            self.i2c.readfrom_mem_into(self.addr, _STATUS_REG, sr, addrsize=16)
            if sr[1] & 0x08:   # bit 3 of low byte = data-ready
                break
        subpage = sr[1] & 0x01
        self._write(_STATUS_REG, 0x0030)
        fd = self._fd_mv
        self._read_chunks_into(_PIXEL_ADDR, fd[0:1536])
        self._read_chunks_into(_AUX_ADDR,   fd[1536:1664], 64)
        return fd, subpage

    def get_frame_data_into(self, out_mv):
        """Like get_frame_data but fills the provided memoryview instead of the internal buffer."""
        i2c  = self.i2c
        addr = self.addr
        sr   = self._sr_buf
        while True:
            i2c.readfrom_mem_into(addr, _STATUS_REG, sr, addrsize=16)
            if sr[1] & 0x08:
                break
        subpage = sr[1] & 0x01
        self._write(_STATUS_REG, 0x0030)
        i2c.readfrom_mem_into(addr, _PIXEL_ADDR, out_mv[0:1536],   addrsize=16)
        i2c.readfrom_mem_into(addr, _AUX_ADDR,   out_mv[1536:1664], addrsize=16)
        return subpage

    # ---------------------------------------------------- temperature calc --

    def calculate_raw(self, fd, subpage, border=0, out=None):
        """
        Fast gain+CP-corrected IR values for motion detection.
        fd is the memoryview from get_frame_data; subpage is the int it returned.
        If out is provided (array.array('f', 768 zeros)) it is reused in-place,
        avoiding allocation. Returns the result array.
        Border/non-subpage pixels are left as 0.0.
        """
        if out is None:
            out = array.array('f', (0.0 for _ in range(768)))
        p    = self.p
        gain = p['gainEE'] / _mv_s16(fd, 778)
        irCP = _mv_s16(fd, 776) * gain if subpage == 0 else _mv_s16(fd, 808) * gain
        tgc  = p['tgc']
        mode = self._mode

        for row in range(border, 24 - border):
            il_pat   = row & 1
            row_base = row << 5        # row * 32
            for col in range(border, 32 - border):
                chess_pat = il_pat ^ (col & 1)
                if (chess_pat if mode else il_pat) != subpage:
                    continue
                pix = row_base | col
                b   = pix << 1
                raw = (fd[b] << 8) | fd[b + 1]
                if raw > 32767: raw -= 65536
                out[pix] = raw * gain - tgc * irCP
        return out

    def get_vdd(self, fd):
        p = self.p
        res_ram = (fd[832] & 0x0C00) >> 10
        res_cor = (1 << p['resolutionEE']) / (1 << res_ram)
        return (res_cor * _s16(fd[810]) - p['vdd25']) / p['kVdd'] + 3.3

    def get_ta(self, fd):
        p = self.p
        vdd  = self.get_vdd(fd)
        ptat = _s16(fd[800])
        ptat_art = ptat / (ptat * p['alphaPTAT'] + _s16(fd[768])) * (1 << 18)
        return (ptat_art / (1 + p['KvPTAT'] * (vdd - 3.3)) - p['vPTAT25']) / p['KtPTAT'] + 25

    def calculate_to(self, fd, emissivity=0.95, tr_offset=-8.0):
        """
        Calculate calibrated object temperatures for all pixels.
        Returns array.array('f', ...) of 768 floats (°C).
        Pixels not belonging to this subpage retain their previous value.
        """
        p      = self.p
        vdd    = self.get_vdd(fd)
        ta     = self.get_ta(fd)
        tr     = ta + tr_offset
        ta4    = (ta + 273.15) ** 4
        tr4    = (tr + 273.15) ** 4
        taTr   = tr4 - (tr4 - ta4) / emissivity

        kta_s  = 1 << p['ktaScale']
        kv_s   = 1 << p['kvScale']
        alpha_s = 1 << p['alphaScale']

        ksTo   = p['ksTo']
        ct     = p['ct']
        alphaCorrR = [
            1.0 / (1 + ksTo[0] * 40),
            1.0,
            1 + ksTo[1] * ct[2],
            0.0,  # set below
        ]
        alphaCorrR[3] = alphaCorrR[2] * (1 + ksTo[2] * (ct[3] - ct[2]))

        gain = p['gainEE'] / _s16(fd[778])

        mode = (fd[832] & 0x1000) >> 5   # 0 = interleaved, 128 = chess
        mode_matches_cal = (mode == p['calibrationModeEE'])

        irCP = [_s16(fd[776]) * gain, _s16(fd[808]) * gain]
        f1 = (1 + p['cpKta'] * (ta - 25)) * (1 + p['cpKv'] * (vdd - 3.3))
        irCP[0] -= p['cpOffset'][0] * f1
        if mode_matches_cal:
            irCP[1] -= p['cpOffset'][1] * f1
        else:
            irCP[1] -= (p['cpOffset'][1] + p['ilChessC'][0]) * f1

        subpage = fd[833]
        sqrt = math.sqrt
        result = array.array('f', (0.0 for _ in range(768)))

        alpha  = p['alpha']
        offset = p['offset']
        kta_a  = p['kta']
        kv_a   = p['kv']
        tgc    = p['tgc']
        KsTa   = p['KsTa']
        il0    = p['ilChessC'][0]
        il1    = p['ilChessC'][1]
        il2    = p['ilChessC'][2]

        for pix in range(768):
            row = pix // 32
            il_pat    = row - (row // 2) * 2          # (pix//32) % 2
            chess_pat = il_pat ^ (pix & 1)
            pattern   = chess_pat if mode else il_pat

            if pattern != subpage:
                continue

            irData = _s16(fd[pix]) * gain
            kta = kta_a[pix] / kta_s
            kv  = kv_a[pix]  / kv_s
            irData -= offset[pix] * (1 + kta * (ta - 25)) * (1 + kv * (vdd - 3.3))

            if not mode_matches_cal:
                conv = ((pix+2)//4 - (pix+3)//4 + (pix+1)//4 - pix//4) * (1 - 2*il_pat)
                irData += il2 * (2*il_pat - 1) - il1 * conv

            irData -= tgc * irCP[subpage]
            irData /= emissivity

            aComp = _SCALEALPHA * alpha_s / alpha[pix]
            aComp *= (1 + KsTa * (ta - 25))

            Sx = sqrt(sqrt(aComp**3 * (irData + aComp * taTr))) * ksTo[1]
            To = sqrt(sqrt(irData / (aComp * (1 - ksTo[1] * 273.15) + Sx) + taTr)) - 273.15

            if   To < ct[1]: rng = 0
            elif To < ct[2]: rng = 1
            elif To < ct[3]: rng = 2
            else:            rng = 3

            To = sqrt(sqrt(irData / (aComp * alphaCorrR[rng] * (1 + ksTo[rng] * (To - ct[rng]))) + taTr)) - 273.15
            result[pix] = To

        return result


# ============================================================= EEPROM extraction ==

def _extract_vdd(ee, p):
    kVdd = _s8(_msb(ee[51]))
    p['kVdd']  = kVdd * 32
    p['vdd25'] = ((_lsb(ee[51]) - 256) << 5) - 8192

def _extract_ptat(ee, p):
    KvPTAT = (ee[50] & 0xFC00) >> 10
    if KvPTAT > 31: KvPTAT -= 64
    p['KvPTAT']   = KvPTAT / 4096.0
    KtPTAT = ee[50] & 0x03FF
    if KtPTAT > 511: KtPTAT -= 1024
    p['KtPTAT']   = KtPTAT / 8.0
    p['vPTAT25']  = ee[49]
    p['alphaPTAT'] = _n4(ee[16]) / (1 << 14) + 8.0

def _extract_gain(ee, p):
    p['gainEE'] = _s16(ee[48])

def _extract_tgc(ee, p):
    p['tgc'] = _s8(_lsb(ee[60])) / 32.0

def _extract_resolution(ee, p):
    p['resolutionEE'] = (ee[56] >> 10) & 0x03

def _extract_ksta(ee, p):
    p['KsTa'] = _s8(_msb(ee[60])) / 8192.0

def _extract_ksto(ee, p):
    step = ((ee[63] & 0x3000) >> 12) * 10
    ct2  = _n2(ee[63]) * step
    p['ct']   = [-40, 0, ct2, ct2 + _n3(ee[63]) * step, 400]
    scale     = 1 << (_n1(ee[63]) + 8)
    p['ksTo'] = [
        _s8(_lsb(ee[61])) / scale,
        _s8(_msb(ee[61])) / scale,
        _s8(_lsb(ee[62])) / scale,
        _s8(_msb(ee[62])) / scale,
        -0.0002,
    ]

def _extract_cp(ee, p):
    alpha_s = _n4(ee[32]) + 27
    o0 = ee[58] & 0x03FF
    if o0 > 511: o0 -= 1024
    o1 = (ee[58] & 0xFC00) >> 10
    if o1 > 31:  o1 -= 64
    o1 += o0
    a0 = ee[57] & 0x03FF
    if a0 > 511: a0 -= 1024
    a0 /= (1 << alpha_s)
    a1 = (ee[57] & 0xFC00) >> 10
    if a1 > 31: a1 -= 64
    a1 = (1 + a1 / 128.0) * a0
    kta_s1 = _n2(ee[56]) + 8
    kv_s   = _n3(ee[56])
    p['cpKta']    = _s8(_lsb(ee[59])) / (1 << kta_s1)
    p['cpKv']     = _s8(_msb(ee[59])) / (1 << kv_s)
    p['cpAlpha']  = [a0, a1]
    p['cpOffset'] = [o0, o1]

def _extract_cilc(ee, p):
    cMode = ((ee[10] & 0x0800) >> 4) ^ 0x80
    p['calibrationModeEE'] = cMode
    c0 = ee[53] & 0x003F
    if c0 > 31: c0 -= 64
    c1 = (ee[53] & 0x07C0) >> 6
    if c1 > 15: c1 -= 32
    c2 = (ee[53] & 0xF800) >> 11
    if c2 > 15: c2 -= 32
    p['ilChessC'] = [c0 / 16.0, c1 / 2.0, c2 / 8.0]

def _extract_alpha(ee, p):
    acc_rem_s = _n1(ee[32])
    acc_col_s = _n2(ee[32])
    acc_row_s = _n3(ee[32])
    alpha_s   = _n4(ee[32]) + 30
    alpha_ref = ee[33]
    tgc       = p['tgc']
    cp_mean   = (p['cpAlpha'][0] + p['cpAlpha'][1]) / 2.0

    acc_row = []
    for i in range(6):
        w = ee[34 + i]
        for j in range(4):
            v = (w >> (4*j)) & 0xF
            if v > 7: v -= 16
            acc_row.append(v)

    acc_col = []
    for i in range(8):
        w = ee[40 + i]
        for j in range(4):
            v = (w >> (4*j)) & 0xF
            if v > 7: v -= 16
            acc_col.append(v)

    alpha_temp = []
    for i in range(24):
        for j in range(32):
            pix = 32*i + j
            v = (ee[64 + pix] & 0x03F0) >> 4
            if v > 31: v -= 64
            v  = v * (1 << acc_rem_s)
            v  = alpha_ref + (acc_row[i] << acc_row_s) + (acc_col[j] << acc_col_s) + v
            v /= (1 << alpha_s)
            v -= tgc * cp_mean
            alpha_temp.append(_SCALEALPHA / v)

    temp = max(alpha_temp)
    scale2 = 0
    while temp < 32767.4:
        temp  *= 2
        scale2 += 1

    p['alpha']      = array.array('H', (int(v * (1 << scale2) + 0.5) for v in alpha_temp))
    p['alphaScale'] = scale2

def _extract_offset(ee, p):
    occ_rem_s = _n1(ee[16])
    occ_col_s = _n2(ee[16])
    occ_row_s = _n3(ee[16])
    off_ref   = _s16(ee[17])

    occ_row = []
    for i in range(6):
        w = ee[18 + i]
        for j in range(4):
            v = (w >> (4*j)) & 0xF
            if v > 7: v -= 16
            occ_row.append(v)

    occ_col = []
    for i in range(8):
        w = ee[24 + i]
        for j in range(4):
            v = (w >> (4*j)) & 0xF
            if v > 7: v -= 16
            occ_col.append(v)

    offsets = []
    for i in range(24):
        for j in range(32):
            pix = 32*i + j
            v = (ee[64 + pix] & 0xFC00) >> 10
            if v > 31: v -= 64
            v  = v * (1 << occ_rem_s)
            v  = off_ref + (occ_row[i] << occ_row_s) + (occ_col[j] << occ_col_s) + v
            offsets.append(v)

    p['offset'] = array.array('h', offsets)

def _extract_kta(ee, p):
    # KtaRC[0]=RoCo, [1]=ReCo, [2]=RoCe, [3]=ReCe (split index ordering)
    KtaRC = [
        _s8(_msb(ee[54])),  # split 0: even row, even col
        _s8(_msb(ee[55])),  # split 1: even row, odd col
        _s8(_lsb(ee[54])),  # split 2: odd row,  even col
        _s8(_lsb(ee[55])),  # split 3: odd row,  odd col
    ]
    kta_s1 = _n2(ee[56]) + 8
    kta_s2 = _n1(ee[56])

    kta_temp = []
    for pix in range(768):
        split = 2 * (pix//32 - (pix//64)*2) + pix % 2
        v = (ee[64 + pix] & 0x000E) >> 1
        if v > 3: v -= 8
        v  = v * (1 << kta_s2)
        v  = (KtaRC[split] + v) / (1 << kta_s1)
        kta_temp.append(v)

    temp = max(abs(v) for v in kta_temp)
    scale = 0
    while temp < 63.4:
        temp  *= 2
        scale += 1

    p['kta']      = array.array('b', (int(v*(1<<scale) - 0.5) if v < 0 else int(v*(1<<scale) + 0.5) for v in kta_temp))
    p['ktaScale'] = scale

def _extract_kv(ee, p):
    KvT = [_n4(ee[52]), _n2(ee[52]), _n3(ee[52]), _n1(ee[52])]
    for i in range(4):
        if KvT[i] > 7: KvT[i] -= 16
    kv_s = _n3(ee[56])

    kv_temp = []
    for pix in range(768):
        split = 2 * (pix//32 - (pix//64)*2) + pix % 2
        kv_temp.append(KvT[split] / (1 << kv_s))

    temp = max(abs(v) for v in kv_temp)
    scale = 0
    while temp < 63.4:
        temp  *= 2
        scale += 1

    p['kv']      = array.array('b', (int(v*(1<<scale) - 0.5) if v < 0 else int(v*(1<<scale) + 0.5) for v in kv_temp))
    p['kvScale'] = scale
