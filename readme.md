# Wavetable Tools (WTT)

This is a toolset for converting and processing wavetables in `.wav` and `.wt` formats. It is not a tool for creating wavetables from scratch, and it is still a work in progress. As such, please use it carefully. I will not be responsible for any damage this programme may cause.

Available tools are:

- printinfo: Print format information to the console. For `.wt` import, some data is assumed to be able to export to `.wav`.
- wttowav: Convert `.wt` wavetables to `.wav` format.
- wavtowt: Convert `.wav` wavetables to `.wt` format.
- addclm: Add `clm ` data to `.wav` wavetables and export to `..._addclm.wav`. 
- slicer: Export individual cycles of a wavetable to a folder.
- dedupe: Removes duplicate cycles from a wavetable if those are in sequence and export to `..._dedupe.wav` or `..._dedupe.wt` (Vital always exports 256 cycles even if the wavetable was made to have fewer cycles and as such makes duplicates of cycles).

Work in progress:
- combiner: Imports individual cycles from a folder and exports to a single wavetable file.

See [this article](https://gist.github.com/iicaras/f63dc9fcc3f9a83ccaf2de3fbc9fbb5a) for format specifications and creation guides.

## printinfo

```
usage: pmain.py printinfo [-h] inpath [inpath ...]

positional arguments:
  inpath      str: Input path(s) to wav or wt file(s) or directory(-ies).

options:
  -h, --help  show this help message and exit
```

Example:

```
python main.py printinfo "Basic Shapes.wav"
```

## wttowav

```
usage: main.py wttowav [-h] [-f] inpath [inpath ...]

positional arguments:
  inpath                str: Input path(s) to wt file(s) or directory(-ies).

options:
  -h, --help            show this help message and exit
  -f, --forceoverwrite  bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.
```

Example:

```
python main.py wttowav "Standard Four.wt"
```

## wavtowt

```
usage: main.py wavtowt [-h] [-f] inpath [inpath ...]

positional arguments:
  inpath                str: Input path(s) to wav file(s) or directory(-ies).

options:
  -h, --help            show this help message and exit
  -f, --forceoverwrite  bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.
```

Example:

```
python main.py wavtowt "Basic Shapes.wav"
```

## addclm

```
usage: main.py addclm [-h] [-f] [--wavesize WAVESIZE] [--waveinterp WAVEINTERP] [--wavevendor WAVEVENDOR] inpath [inpath ...]

positional arguments:
  inpath                str: Input path(s) to wav file(s) or directory(-ies).

options:
  -h, --help            show this help message and exit
  -f, --forceoverwrite  bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.
  --wavesize WAVESIZE   int: Samples per wave cycle. Default: 2048.
  --waveinterp WAVEINTERP
                        int: Interpolation between cycles. Default: 0.
  --wavevendor WAVEVENDOR
                        str: Comment at the end of clm chunk. Default: b'wavetable (wavetabletools)'.
```

Example:

```
python main.py addclm "Custom.wav" --wavevendor "My Wavetable"
```

## slicer

```
usage: main.py slicer [-h] [-f] [--wavesize WAVESIZE] inpath [inpath ...]

positional arguments:
  inpath                str: Input path(s) to wav or wt file(s) or directory(-ies).

options:
  -h, --help            show this help message and exit
  -f, --forceoverwrite  bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.
  --wavesize WAVESIZE   int: Samples per wave cycle. If not present in .wav clm data, this needs to be supplied.
```

Example:

```
python main.py slicer "Basic Shapes.wav"
```

## dedupe

```
usage: main.py dedupe [-h] [-f] inpath [inpath ...]

positional arguments:
  inpath                str: Input path(s) to directory(-ies).

options:
  -h, --help            show this help message and exit
  -f, --forceoverwrite  bool: Force-overwrite target file(s) if file(s) already exist(s). Default: false.
```

Example:

```
python main.py dedupe "Custom.wav"
```
