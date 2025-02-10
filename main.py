"""Add combiner, which would take all numbered wav files from a folder and make a wavetable from it.
"""
import logging
import argparse
import os


class Wavetable():
    """Class is meant to collect the following data as attributes:
        - data_samples          [bytes]     Actual sample PCM data.
        - fmt_audio_format      [int]       1 is PCM, 3 is IEEE 754 Float. PCM is preferred.
        - fmt_bits_p_sample     [int]       How many bits are used to describe the amplitude of a sample point. Usually 16.
        - fmt_bytes_p_block     [int]       Bytes per Block (Number of Channels * Bits per sample / 8). Stored for the convenience of easy access when needed.
        - fmt_bytes_p_sec       [int]       Bytes to Read per Second (Sample Rate * Bytes per Block). Stored for the convenience of easy access when needed.
        - fmt_channels          [int]       Number of Channels such as left and right. 1 is preferred and assumed for wt import.
        - fmt_sample_rate       [int]       Samples per Second. 44100 samples/s is preferred. Vital exports as 88200 samples/sec. In principle it doesn't really matter since wave_size matters more for the synth.
        - wave_count            [int]       Number of wave cycles in the sample data.
        - wave_interp           [int]       Interpolation between cycles. 0 = no interpolation, 1 = linear crossfades, 2,3,4 = spectral morph. It's just metadata and doesn't say anything about the sample data itself.
        - wave_size             [int]       Samples per wave cycle. 2048 is the standard but any power of 2 is usually easily read.
        - wave_vendor           [bytes]     There is some space in the clm data chunk to write a comment. Serum and Vital write vendor info. This class by default writes b'wavetable (wavetabletools)'. I think the clm chunk needs to be an even number in length for some synths to read the wavetable.

    Class only cares about the following wav chunks:
        - riff                              General file information.
        - fmt                               Wave format information.
        - clm                               Wavetable information.
        - data                              Sample data.
    The rest, such as smpl or junk, is not read nor written.

    The wt format essentially stores the same PCM data, however, with different header information. When reading wt, the following data is assumed:
        - fmt_audio_format  = 1
        - fmt_channels      = 1
        - fmt_sample_rate   = 44100
        - fmt_bytes_p_block = int(self.fmt_channels * self.fmt_bits_p_sample / 8)
        - fmt_bytes_p_sec   = int(self.fmt_sample_rate * self.fmt_bytes_p_block)
        - wave_interp       = 0
        - wave_vendor       = b'wavetable (wavetabletools)'

    For wt reading or writing, the following (flags) are not supported:
        - wt is a sample. Programme exits when reading. Assumed False when writing.
        - Looped samples are not supported. Programme exits when reading. Assumed False when writing.
        - More than 1 channels. Programme exits when writing.
        - full-range classification. Wavetables are always processed with full 16-bit range. Pass when reading. Assumed True when writing.
        - wave_size is not a power of 2 such as 2048. Programme exits when writing.
    """

    def __init__(self):
        self.data_samples      = None
        self.fmt_audio_format  = None
        self.fmt_bits_p_sample = None
        self.fmt_bytes_p_block = None
        self.fmt_bytes_p_sec   = None
        self.fmt_channels      = None
        self.fmt_sample_rate   = None
        self.wave_count        = None
        self.wave_interp       = 0                                              # Set default clm
        self.wave_size         = 2048                                           # Set default clm
        self.wave_vendor       = b'wavetable (wavetabletools)'                  # Set default clm

    def wav_import(self, file_path):
        """Reads byte per byte until it finds a chunk header. open_file.seek(-3, os.SEEK_CUR) in wav_parse_chunk() ensures this.
        return: True if file needs to be skipped due to unsupported format. Else None.
        """
        log.info(f'Reading {file_path}')
        with open(file_path, 'rb') as open_file:
            while True:
                chunk_id = open_file.read(4)
                if not len(chunk_id) == 4:
                    break
                stop_importing = self.wav_parse_chunk(open_file, chunk_id)
                if stop_importing:
                    return True
        if self.wave_size:
            self.wave_count = self.calc_wave_count()                            # Number of waves

    def wav_parse_chunk(self, open_file, chunk_id):
        """return: True if file needs to be skipped due to unsupported format. Else None.
        """
        if self.is_riff(chunk_id):                                              # [4] RIFF
            log.info('    Found \'riff\' chunk.')
            open_file.seek(4, os.SEEK_CUR)                                      # [4] File Size -8 Bytes (Padding for now)
            if open_file.read(4) != b'WAVE':                                    # [4] WAVE
                log.warning('File not in WAVE format.')
                return True

        elif self.is_fmt(chunk_id):                                             # [4] fmt
            log.info('    Found \'fmt \' chunk.')
            open_file.seek(4, os.SEEK_CUR)                                      # [4] fmt Chunk Size -8 Bytes
            self.fmt_audio_format  = int.from_bytes(open_file.read(2), 'little')  # [2] Audio Format. 01: PCM, 11: IEEE 754 Float
            self.fmt_channels      = int.from_bytes(open_file.read(2), 'little')  # [2] Number of Channels
            self.fmt_sample_rate   = int.from_bytes(open_file.read(4), 'little')  # [4] Samples per Second
            self.fmt_bytes_p_sec   = int.from_bytes(open_file.read(4), 'little')  # [4] Bytes to Read per Second (Sample Rate * Bytes per Block)
            self.fmt_bytes_p_block = int.from_bytes(open_file.read(2), 'little')  # [2] Bytes per Block (Number of Channels * Bits per sample / 8)
            self.fmt_bits_p_sample = int.from_bytes(open_file.read(2), 'little')  # [2] Bits per Sample

        elif self.is_clm(chunk_id):                                             # [4] clm
            log.info('    Found \'clm \' chunk.')
            clm_size = int.from_bytes(open_file.read(4), 'little')              # [4] clm chunk size -8 Bytes
            clm_data = open_file.read(clm_size)                                 # [#] clm ansi bytestring data
            self.wave_size   = int(clm_data[3:7])                               # Samples per wave
            self.wave_interp = int(clm_data[8:9])                               # Vital: 0: None. 1: Time. 2, 3, 4: Spectral.
            self.wave_vendor = clm_data[17:]                                    # Vendor bytestring

        elif self.is_data(chunk_id):                                            # [4] data
            data_size         = int.from_bytes(open_file.read(4), 'little')     # [4] Sample Size
            if not self.data_samples:
                log.info('    Found \'data\' chunk.')
                self.data_samples = open_file.read(data_size)                   # [#] Sample Data
            else:
                log.warning('    Other data tag skipped. Check if correct data was fetched.')

        else:
            open_file.seek(-3, os.SEEK_CUR)

    def is_riff(self, chunk_id):
        return chunk_id == bytes.fromhex('52 49 46 46')

    def is_fmt(self, chunk_id):
        return chunk_id == bytes.fromhex('66 6D 74 20')

    def is_clm(self, chunk_id):
        return chunk_id == bytes.fromhex('63 6C 6D 20')

    def is_data(self, chunk_id):
        return chunk_id == bytes.fromhex('64 61 74 61')

    def is_junk(self, chunk_id):
        return chunk_id == bytes.fromhex('4A 55 4E 4B')

    def wt_import(self, file_path):
        """return: True if file needs to be skipped due to unsupported format. Else None.
        """
        log.info(f'Reading {file_path}')
        with open(file_path, 'rb') as open_file:
            open_file.seek(4, os.SEEK_SET)                                      # [4] vawt
            self.wave_size  = int.from_bytes(open_file.read(4), 'little')       # [4] Samples per wave
            self.wave_count = int.from_bytes(open_file.read(2), 'little')       # [2] Number of waves

            flags = int.from_bytes(open_file.read(2), 'little')                 # [2] Flags
            stop_importing = self.wt_parse_flags(flags)
            if stop_importing:
                return True

            self.data_samples = open_file.read(-1)                              # [#] Sample Data

            log.info('Assume \'fmt \' chunk data, wave_interp = 0, and add wave_vendor b\'wavetable (wavetabletools)\'.')
            self.fmt_audio_format  = 1                                          # Audio Format. 01: PCM, 11: IEEE 754 Float
            self.fmt_channels      = 1                                          # Number of Channels
            self.fmt_sample_rate   = 44100                                      # Samples per Second
            self.fmt_bytes_p_block = self.calc_fmt_bytes_p_block()              # Bytes per Block (Number of Channels * Bits per sample / 8)
            self.fmt_bytes_p_sec   = self.calc_fmt_bytes_p_sec()                # Bytes to Read per Second (Sample Rate * Bytes per Block)

    def wt_parse_flags(self, flags):
        """return: True if file needs to be skipped due to unsupported format. Else None.
        """
        if self.is_sample(flags):                                               # Is sample or wavetable
            log.warning('Wavetable is a sample.')
            return True

        if self.is_looped(flags):                                               # Is looped sample
            log.warning('Wavetable is a sample.')
            return True

        if self.is_int16(flags):                                                # 16 bits per sample if set, else float32
            self.fmt_bits_p_sample = 16
        else:
            self.fmt_bits_p_sample = 32

        if self.is_full_range(flags):                                           # Full 16 bit peak range if data is int16 if set. Else uses 15 bits which is -6 dBFS peak.
            pass

    def is_sample(self, flags):
        return flags & 1 != 0

    def is_looped(self, flags):
        return flags & 2 != 0

    def is_int16(self, flags):
        return flags & 4 != 0

    def is_full_range(self, flags):
        return flags & 8 != 0

    def calc_fmt_bytes_p_block(self):
        return int(self.fmt_channels * self.fmt_bits_p_sample / 8)              # Bytes per Block (Number of Channels * Bits per sample / 8)

    def calc_fmt_bytes_p_sec(self):
        return int(self.fmt_sample_rate * self.fmt_bytes_p_block)               # Bytes to Read per Second (Sample Rate * Bytes per Block)

    def calc_wave_count(self):
        return int(len(self.data_samples) / (self.wave_size * self.fmt_bytes_p_block))

    def wav_write(self, file_path):
        clm_string = f'<!>{self.wave_size} {self.wave_interp}0000000 '
        clm_data   = clm_string.encode(encoding='ansi') + self.wave_vendor
        if len(clm_data) % 2 == 1:
            clm_data += bytes.fromhex('00')                                     # Vital desn't read the wavetable properly when its length is odd.
        log.info(f'Writing {file_path}.')
        with open(file_path, 'wb') as open_file:
            log.info('    Writing riff.')
            open_file.write(bytes.fromhex('52 49 46 46'))                       # [4] RIFF
            open_file.write(bytes.fromhex('00 00 00 00'))                       # [4] File Size -8 Bkytes (Padding for now)
            open_file.write(bytes.fromhex('57 41 56 45'))                       # [4] WAVE

            log.info('    Writing fmt.')
            open_file.write(bytes.fromhex('66 6D 74 20'))                       # [4] fmt
            open_file.write(bytes.fromhex('10 00 00 00'))                       # [4] fmt Chunk Size -8 Bytes
            open_file.write(self.fmt_audio_format.to_bytes(2, 'little'))        # [2] Audio Format. 01: PCM, 11: IEEE 754 Float
            open_file.write(self.fmt_channels.to_bytes(2, 'little'))            # [2] Number of Channels
            open_file.write(self.fmt_sample_rate.to_bytes(4, 'little'))         # [4] Samples per Second
            open_file.write(self.fmt_bytes_p_sec.to_bytes(4, 'little'))         # [4] Bytes to Read per Second (Sample Rate * Bytes per Block)
            open_file.write(self.fmt_bytes_p_block.to_bytes(2, 'little'))       # [2] Bytes per Block (Number of Channels * Bits per sample / 8)
            open_file.write(self.fmt_bits_p_sample.to_bytes(2, 'little'))       # [2] Bits per Sample

            log.info('    Writing clm.')
            open_file.write(bytes.fromhex('63 6C 6D 20'))                       # [4] clm
            open_file.write(len(clm_data).to_bytes(4, 'little'))                # [4] clm chunk size -8 Bytes
            open_file.write(clm_data)                                           # [#] clm ansi bytestring data

            log.info('    Writing data.')
            open_file.write(bytes.fromhex('64 61 74 61'))                       # [4] data
            open_file.write(len(self.data_samples).to_bytes(4, 'little'))       # [4] Sample Size
            open_file.write(self.data_samples)                                  # [#] Sample Data

            log.info('    Calc size.')
            open_file.seek(0, os.SEEK_END)                                      # Go to file end
            file_size = open_file.tell() - 8                                    # Get current position of file object as int
            open_file.seek(4, os.SEEK_SET)                                      # Go to the 4th byte for File Size
            open_file.write(file_size.to_bytes(4, 'little'))                    # Write File Size

    def wt_set_flag(self, is_sample, is_looped, is_full_range):
        flag = 0
        if is_sample:                                                           # Is sample or wavetable
            flag = flag | 1
        if is_looped:                                                           # Is looped sample
            flag = flag | 2
        if self.fmt_bits_p_sample == 16:                                        # 16 bits per sample if set, else float32
            flag = flag | 4
            if is_full_range:                                                   # Full 16 bit peak range if data is int16 if set. Else uses 15 bits which is -6 dBFS peak.
                flag = flag | 8
        return flag

    def wt_write(self, file_path, is_sample=False, is_looped=False, is_full_range=True):
        if self.fmt_channels != 1:
            log.warning('Only 1 channel is supported.')
            return
        if (self.wave_size & (self.wave_size - 1) != 0) or self.wave_size == 0:
            log.warning('Wave size must be a power of 2.')
            return
        with open(file_path, 'wb') as open_file:
            log.info(f'Writing {file_path}.')
            open_file.write(bytes.fromhex('76 61 77 74'))                       # [4] vawt
            open_file.write(self.wave_size.to_bytes(4, 'little'))               # [4] Samples per wave
            open_file.write(self.wave_count.to_bytes(2, 'little'))              # [2] Number of waves
            open_file.write(self.wt_set_flag(is_sample, is_looped, is_full_range).to_bytes(2, 'little'))  # [2] Flags
            open_file.write(self.data_samples)                                  # [#] Sample Data

    def print_wavetable_info(self):
        log.info('Wavetable info:')
        for k, v in sorted(vars(self).items()):
            if k != 'data_samples':
                log.info(f'    {k}: {v}')

    def slicer(self):
        if self.wave_size is None:
            log.warning('wave_size not in wavetable. 2048 samples is assumed. Use --wavesize to supply a different wave_size.')
            self.wave_size = 2048
        cycles = [self.data_samples[i:i + self.wave_size * self.fmt_bytes_p_block] for i in range(0, len(self.data_samples), self.wave_size * self.fmt_bytes_p_block)]
        return cycles

    def wav_export_cycles(self, outpath_folder):
        os.makedirs(outpath_folder, exist_ok=True)
        data_samples_total_temp = self.data_samples
        for cycle_num, cycles_data in enumerate(self.slicer()):
            self.data_samples = cycles_data
            outpath = os.path.join(outpath_folder, f'{cycle_num}.wav')
            self.wav_write(outpath)
        self.data_samples = data_samples_total_temp

    def deduplicator(self):
        """return: True if no duplicates found. Else None.
        """
        cycles_all    = self.slicer()
        cycles_dedupe = [cycles_all[0]]
        for cycle in cycles_all[1:]:
            if cycle != cycles_dedupe[-1]:
                cycles_dedupe.append(cycle)
        if len(cycles_all) == len(cycles_dedupe):
            log.info('No duplicates found.')
            return True
        else:
            log.info('Set data_samples:')
            self.data_samples = b''.join(cycles_dedupe)
            self.wave_interp  = 0
            self.wave_count   = len(cycles_dedupe)
            log.info('Set clm data:')
            log.info(f'    wave_interp: {self.wave_interp}')
            log.info(f'    wave_count: {self.wave_count}')


def get_clas(arg=None):
    """return: Argparse class.
    """
    desc   = 'Wavetable Tools: Various tools to convert or process wavetables in wav or wt format.'
    parser = argparse.ArgumentParser(prog='main.py', description=desc, epilog='')

    subparsers = parser.add_subparsers(dest="programme", help='Available programmes.')

    subparsers_print_info   = subparsers.add_parser('printinfo', help='Print wavetable info.')
    subparsers_print_info.add_argument('inpath', type=str, nargs='+', help='str: Input path(s) to wav or wt file(s) or directory(-ies).')

    subparsers_wt_to_wav    = subparsers.add_parser('wttowav', help='Convert wt wavetables to wav.')
    subparsers_wt_to_wav.add_argument('inpath', type=str, nargs='+', help='str: Input path(s) to wt file(s) or directory(-ies).')
    subparsers_wt_to_wav.add_argument('-f', '--forceoverwrite', action='store_true', help='bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.')
    subparsers_wt_to_wav.add_argument('--wavevendor', type=str, help='str: Comment at the end of clm chunk. Default: \'wavetable (wavetabletools)\'.')

    subparsers_wav_to_wt    = subparsers.add_parser('wavtowt', help='Convert wav wavetables to wt.')
    subparsers_wav_to_wt.add_argument('inpath', type=str, nargs='+', help='str: Input path(s) to wav file(s) or directory(-ies).')
    subparsers_wav_to_wt.add_argument('-f', '--forceoverwrite', action='store_true', help='bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.')

    subparser_add_clm       = subparsers.add_parser('addclm', help='Add clm chunk to a wav files, which will be written to {inpath}_addclm.wav. Note that optional args will be written to all supplied files.')
    subparser_add_clm.add_argument('inpath', type=str, nargs='+', help='str: Input path(s) to wav file(s) or directory(-ies).')
    subparser_add_clm.add_argument('-f', '--forceoverwrite', action='store_true', help='bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.')
    subparser_add_clm.add_argument('--wavesize', type=int, help='int: Samples per wave cycle. Default: 2048.')
    subparser_add_clm.add_argument('--waveinterp', type=int, help='int: Interpolation between cycles. Default: 0.')
    subparser_add_clm.add_argument('--wavevendor', type=str, help='str: Comment at the end of clm chunk. Default if no prior clm info in the wavetable: \'wavetable (wavetabletools)\'.')

    subparser_slicer        = subparsers.add_parser('slicer', help='Slice wavetables and export individual cycles to {inpath}/#.wav.')
    subparser_slicer.add_argument('inpath', type=str, nargs='+', help='str: Input path(s) to wav or wt file(s) or directory(-ies).')
    subparser_slicer.add_argument('-f', '--forceoverwrite', action='store_true', help='bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.')
    subparser_slicer.add_argument('--wavesize', type=int, help='int: Samples per wave cycle. If not present in .wav clm data, this needs to be supplied.')

    subparser_combiner      = subparsers.add_parser('combiner', help='Combine wav cycles and export to wav and/or wt.')
    subparser_combiner.add_argument('inpath', type=str, nargs='+', help='str: Input path(s) to directory(-ies).')
    subparser_combiner.add_argument('-f', '--forceoverwrite', action='store_true', help='bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.')

    subparser_dedupe  = subparsers.add_parser('dedupe', help='Remove duplicate cycles.')
    subparser_dedupe.add_argument('inpath', type=str, nargs='+', help='str: Input path(s) to directory(-ies).')
    subparser_dedupe.add_argument('-f', '--forceoverwrite', action='store_true', help='bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.')
    subparser_dedupe.add_argument('--wavevendor', type=str, help='str: Comment at the end of clm chunk.')
    return parser.parse_args(arg)


def main(args):
    log.info('WTT Version 2025021000.')
    match args.programme:
        case 'printinfo'    : print_info(args)
        case 'wttowav'      : wt_to_wav(args)
        case 'wavtowt'      : wav_to_wt(args)
        case 'addclm'       : add_clm(args)
        case 'slicer'       : slicer(args)
        case 'combiner'     : combiner(args)
        case 'dedupe'       : dedupe(args)
        case None: get_clas(['-h'])


def handler_file_dir(inpaths_from_args):
    inpaths = []
    for inpath in inpaths_from_args:
        inpath_abs = os.path.abspath(inpath)
        if os.path.isfile(inpath_abs):
            inpaths.append(inpath_abs)
        elif os.path.isdir(inpath_abs):
            files_in_indir = next(os.walk(inpath_abs), (None, None, []))[2]     # [] if no file https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
            inpaths += [os.path.join(inpath_abs, p) for p in files_in_indir]
        else:
            log.error('Given inpath is not a file or directory.')
            exit()
    log.debug(inpaths)
    return inpaths


def overwrite(outpath, force_overwrite):
    if force_overwrite:
        return True
    if os.path.exists(outpath):
        log.warning(f'{outpath} already exists.')
        return {"Y": True, "y": True, "N": False, "n": False}.get(input('               > Overwrite? (Y/N): '), False)
    else:
        return True


def print_info(args):
    log.info('Programme print.')
    inpaths = handler_file_dir(args.inpath)
    for inpath in inpaths:
        log.info('')
        wavetable_instance = Wavetable()
        if inpath.endswith('.wav'):
            skip = wavetable_instance.wav_import(inpath)
        elif inpath.endswith('.wt'):
            skip = wavetable_instance.wt_import(inpath)
        else:
            log.warning(f'{inpath} is not a wav or wt file.')
            continue
        if skip:
            log.warning('File skipped.')
            continue
        wavetable_instance.print_wavetable_info()


def wt_to_wav(args):
    log.info('Programme wttowav.')
    inpaths = handler_file_dir(args.inpath)
    for inpath in inpaths:
        log.info('')
        if not inpath.endswith('.wt'):
            log.warning(f'{inpath} is not a wt file.')
            continue
        outpath = os.path.abspath(os.path.splitext(inpath)[0] + '.wav')
        wavetable_instance = Wavetable()
        skip = wavetable_instance.wt_import(inpath)
        if skip:
            log.warning('File skipped.')
            continue
        wavetable_instance.wave_vendor = args.wavevendor.encode(encoding='ansi') if args.wavevendor else wavetable_instance.wave_vendor
        wavetable_instance.print_wavetable_info()
        if not overwrite(outpath, args.forceoverwrite):
            log.warning('File Skipped.')
            continue
        wavetable_instance.wav_write(outpath)


def wav_to_wt(args):
    log.info('Programme wavtowt.')
    inpaths = handler_file_dir(args.inpath)
    for inpath in inpaths:
        log.info('')
        if not inpath.endswith('.wav'):
            log.warning(f'{inpath} is not a wav file.')
            continue
        outpath = os.path.abspath(os.path.splitext(inpath)[0] + '.wt')
        wavetable_instance = Wavetable()
        skip = wavetable_instance.wav_import(inpath)
        if skip:
            log.warning('File skipped.')
            continue
        wavetable_instance.print_wavetable_info()
        if not overwrite(outpath, args.forceoverwrite):
            log.warning('File Skipped.')
            continue
        wavetable_instance.wt_write(outpath)


def add_clm(args):
    log.info('Programme addclm.')
    inpaths = handler_file_dir(args.inpath)
    for inpath in inpaths:
        log.info('')
        if not inpath.endswith('.wav'):
            log.warning(f'{inpath} is not a wav file.')
            continue
        outpath = os.path.abspath(os.path.splitext(inpath)[0] + '_addclm.wav')
        wavetable_instance = Wavetable()
        skip = wavetable_instance.wav_import(inpath)
        if skip:
            log.warning('File skipped.')
            continue
        log.info('Set clm data.')
        if args.waveinterp:
            wavetable_instance.wave_interp = args.waveinterp
        if args.wavesize:
            wavetable_instance.wave_size   = args.wavesize
        if args.wavevendor:
            wavetable_instance.wave_vendor = args.wavevendor.encode(encoding='ansi')
        wavetable_instance.print_wavetable_info()
        if not overwrite(outpath, args.forceoverwrite):
            log.warning('File Skipped.')
            continue
        wavetable_instance.wav_write(outpath)


def slicer(args):
    log.info('Programme slicer.')
    inpaths = handler_file_dir(args.inpath)
    for inpath in inpaths:
        log.info('')
        inpath_no_ext, ext = os.path.splitext(inpath)
        outpath_folder = os.path.abspath(inpath_no_ext + ext.replace('.', '_') + '_cycles')
        wavetable_instance = Wavetable()
        if inpath.endswith('.wav'):
            skip = wavetable_instance.wav_import(inpath)
        elif inpath.endswith('.wt'):
            skip = wavetable_instance.wt_import(inpath)
        else:
            log.warning(f'{inpath} is not a wav or wt file.')
            continue
        if skip:
            log.warning('File skipped.')
            continue
        if args.wavesize is not None:
            wavetable_instance.wave_size = args.wavesize
            log.info(f'Set wave_size: {wavetable_instance.wave_size}')
        wavetable_instance.print_wavetable_info()
        if not overwrite(outpath_folder, args.forceoverwrite):
            log.warning('File Skipped.')
            continue
        wavetable_instance.wav_export_cycles(outpath_folder)


def combiner(args):
    pass


def dedupe(args):
    log.info('Programme dedupe.')
    inpaths = handler_file_dir(args.inpath)
    for inpath in inpaths:
        log.info('')
        wavetable_instance = Wavetable()
        if inpath.endswith('.wav'):
            outpath = os.path.abspath(os.path.splitext(inpath)[0] + '_dedupe.wav')
            skip = wavetable_instance.wav_import(inpath)
            if skip:
                log.warning('File skipped.')
                continue
            no_dupe = wavetable_instance.deduplicator()
            if no_dupe:
                continue
            wavetable_instance.wave_vendor = args.wavevendor.encode(encoding='ansi') if args.wavevendor else wavetable_instance.wave_vendor
            wavetable_instance.print_wavetable_info()
            if not overwrite(outpath, args.forceoverwrite):
                log.warning('File Skipped.')
                continue
            wavetable_instance.wav_write(outpath)
        elif inpath.endswith('.wt'):
            outpath = os.path.abspath(os.path.splitext(inpath)[0] + '_dedupe.wt')
            skip = wavetable_instance.wt_import(inpath)
            if skip:
                log.warning('File skipped.')
                continue
            wavetable_instance.print_wavetable_info()
            no_dupe = wavetable_instance.deduplicator()
            if no_dupe:
                continue
            if not overwrite(outpath, args.forceoverwrite):
                log.warning('File Skipped.')
                continue
            wavetable_instance.wt_write(outpath)
        else:
            log.warning(f'{inpath} is not a wav or wt file.')
            continue


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s]: %(message)s')  # filename='main.log'
    log = logging.getLogger(__name__)
    try:
        args = get_clas()
        main(args)
    except Exception as e:
        log.exception(e)
