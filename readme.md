# Wavetable Tools (WTT)

This is a toolset written in Python for making, converting and processing wavetables in `.wav` and `.wt` formats. It is not a tool for creating wavetables from scratch, however it can turn samples into wavetables. It was born out of a lack for wavetable creation tools in Bitwig, and out of some annoyences with Vital's exports. It is still a work in progress. As such, please use it carefully. I will not be responsible for any damage this programme may cause.

A Python installation is required.

Available tools are:

- printinfo: Print wavetable info.
- maketable: Convert sample to wav wavetable.
- wttowav:   Convert wt wavetables to wav.
- wavtowt:   Convert wav wavetables to wt.
- addclm:    Add clm chunk to wav files, which will be written to `{inpath}_addclm.wav`. Note that optional args will be written to all supplied files.
- slicer:    Slice wavetables and export individual cycles to `{inpath}/#.wav`.
- combiner:  Combine wav cycles and export to wav and/or wt.
- dedupe:    Remove duplicate cycles, which will be written to `{inpath}_dedupe.wav`. (Vital always exports 256 cycles even if the wavetable was made to have fewer cycles and as such makes duplicates of cycles).

It is possible to process multiple wavetables in bulk simply by supplying multiple files. For instance,

```
python wtt.py printinfo "some_wavetable.wav" "some_other_wavetable.wav" "another_wavetable.wav"
```

Work in progress:
- combiner: Imports individual cycles from a folder and exports to a single wavetable file.
- use of notes to specify `wave_size` and perhaps use Sox integration to resample to 2048 samples per cycle.

See [this article](https://gist.github.com/iicaras/f63dc9fcc3f9a83ccaf2de3fbc9fbb5a) for format specifications and creation guides.

## printinfo

```
usage: wtt.py printinfo [-h] inpath [inpath ...]

positional arguments:
  inpath      str: Input path(s) to wav or wt file(s) or directory(-ies).

options:
  -h, --help  show this help message and exit
```

Example:

```
python wtt.py printinfo "some_wavetable.wav"
```

## maketable

```
usage: wtt.py maketable [-h] [-f] [--samplerate SAMPLERATE] [--waveinterp WAVEINTERP] [--wavesize WAVESIZE] [--wavevendor WAVEVENDOR] [--wt] [--right] inpath [inpath ...]

positional arguments:
  inpath                str: Input path(s) to wav file(s) or directory(-ies).

options:
  -h, --help            show this help message and exit
  -f, --forceoverwrite  bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.
  --samplerate SAMPLERATE
                        int: Change sample rate. This does not resample the file. Sample rate is meaningless for the wavetable due to wave_size, but a higher sample rate will playback a higher note outside
                        of wavetable synths.
  --waveinterp WAVEINTERP
                        int: Interpolation between cycles. Default: 0.
  --wavesize WAVESIZE   int: Samples per wave cycle. 2048 is assumed if no clm data is present.
  --wavevendor WAVEVENDOR
                        str: Comment at the end of clm chunk.
  --wt                  bool: Also export wt file.
  --right               bool: use right channel instead of left.
```

Example:

`python wtt.py maketable "some_wavetable.wav" --wt`

## wttowav

```
usage: wtt.py wttowav [-h] [-f] [--samplerate SAMPLERATE] [--waveinterp WAVEINTERP] [--wavesize WAVESIZE] [--wavevendor WAVEVENDOR] inpath [inpath ...]

positional arguments:
  inpath                str: Input path(s) to wt file(s) or directory(-ies).

options:
  -h, --help            show this help message and exit
  -f, --forceoverwrite  bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.
  --samplerate SAMPLERATE
                        int: Change sample rate. This does not resample the file. Sample rate is meaningless for the wavetable due to wave_size, but a higher sample rate will playback a higher note outside
                        of wavetable synths.
  --waveinterp WAVEINTERP
                        int: Interpolation between cycles. Default: 0.
  --wavesize WAVESIZE   int: Samples per wave cycle. 2048 is assumed if no clm data is present.
  --wavevendor WAVEVENDOR
                        str: Comment at the end of clm chunk.
```

Example:

```
python wtt.py wttowav "some_wavetable.wt"
```

## wavtowt

```
usage: wtt.py wavtowt [-h] [-f] [--samplerate SAMPLERATE] [--waveinterp WAVEINTERP] [--wavesize WAVESIZE] [--wavevendor WAVEVENDOR] inpath [inpath ...]

positional arguments:
  inpath                str: Input path(s) to wav file(s) or directory(-ies).

options:
  -h, --help            show this help message and exit
  -f, --forceoverwrite  bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.
  --samplerate SAMPLERATE
                        int: Change sample rate. This does not resample the file. Sample rate is meaningless for the wavetable due to wave_size, but a higher sample rate will playback a higher note outside
                        of wavetable synths.
  --waveinterp WAVEINTERP
                        int: Interpolation between cycles. Default: 0.
  --wavesize WAVESIZE   int: Samples per wave cycle. 2048 is assumed if no clm data is present.
  --wavevendor WAVEVENDOR
                        str: Comment at the end of clm chunk.
```

Example:

```
python wtt.py wavtowt "some_wavetable.wav"
```

## addclm

```
usage: wtt.py addclm [-h] [-f] [--samplerate SAMPLERATE] [--waveinterp WAVEINTERP] [--wavesize WAVESIZE] [--wavevendor WAVEVENDOR] inpath [inpath ...]

positional arguments:
  inpath                str: Input path(s) to wav file(s) or directory(-ies).

options:
  -h, --help            show this help message and exit
  -f, --forceoverwrite  bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.
  --samplerate SAMPLERATE
                        int: Change sample rate. This does not resample the file. Sample rate is meaningless for the wavetable due to wave_size, but a higher sample rate will playback a higher note outside
                        of wavetable synths.
  --waveinterp WAVEINTERP
                        int: Interpolation between cycles. Default: 0.
  --wavesize WAVESIZE   int: Samples per wave cycle. 2048 is assumed if no clm data is present.
  --wavevendor WAVEVENDOR
                        str: Comment at the end of clm chunk.
```

Example:

```
python wtt.py addclm "some_wavetable.wav" --wavevendor "wavetable (myname)"
```

## slicer

```
usage: wtt.py slicer [-h] [-f] [--samplerate SAMPLERATE] [--waveinterp WAVEINTERP] [--wavesize WAVESIZE] [--wavevendor WAVEVENDOR] inpath [inpath ...]

positional arguments:
  inpath                str: Input path(s) to wav or wt file(s) or directory(-ies).

options:
  -h, --help            show this help message and exit
  -f, --forceoverwrite  bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.
  --samplerate SAMPLERATE
                        int: Change sample rate. This does not resample the file. Sample rate is meaningless for the wavetable due to wave_size, but a higher sample rate will playback a higher note outside
                        of wavetable synths.
  --waveinterp WAVEINTERP
                        int: Interpolation between cycles. Default: 0.
  --wavesize WAVESIZE   int: Samples per wave cycle. 2048 is assumed if no clm data is present.
  --wavevendor WAVEVENDOR
                        str: Comment at the end of clm chunk.
```

Example:

```
python wtt.py slicer "some_wavetable.wav"
```

## dedupe

```
usage: wtt.py dedupe [-h] [-f] [--samplerate SAMPLERATE] [--waveinterp WAVEINTERP] [--wavesize WAVESIZE] [--wavevendor WAVEVENDOR] inpath [inpath ...]

positional arguments:
  inpath                str: Input path(s) to directory(-ies).

options:
  -h, --help            show this help message and exit
  -f, --forceoverwrite  bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.
  --samplerate SAMPLERATE
                        int: Change sample rate. This does not resample the file. Sample rate is meaningless for the wavetable due to wave_size, but a higher sample rate will playback a higher note outside
                        of wavetable synths.
  --waveinterp WAVEINTERP
                        int: Interpolation between cycles. Default: 0.
  --wavesize WAVESIZE   int: Samples per wave cycle. 2048 is assumed if no clm data is present.
  --wavevendor WAVEVENDOR
                        str: Comment at the end of clm chunk.
```

Example:

```
python wtt.py dedupe "some_wavetable.wav"
```