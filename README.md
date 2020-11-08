PIDRILA
=========

Current Release: v0.1.0 (2020.11.08)

Overview
--------
**PIDRILA**: **P**ython **I**nteractive **D**eepweb-oriented **R**apid **I**ntelligent **L**ink **A**nalyzer is really fast async web path scanner prototype 
developed by BrightSearch team for all ethical netstalkers.

Installation & Usage
------------

```
git clone https://github.com/enemy-submarine/pidrila.git
cd pidrila
python3 pidrila.py -u <URL>
```

Options
-------

```
Usage: pidrila.py [OPTIONS]

Options:
  -U, --user-agent TEXT           User-Agent
  -t, --timeout INTEGER           Request timeout  [default: 30]
  -A, --auth TEXT                 Basic HTTP auth, i.e. login:password
  -M, --max-connections-per-host INTEGER
                                  How many simultaneous connections should we
                                  open (per each host)  [default: 16]

  -m, --max-connections INTEGER   How many simultaneous connections should we
                                  open  [default: 128]

  -p, --proxy TEXT                Proxy address, like socks5h://127.0.0.1:9050
  -p, --pathlist FILENAME         Path list
  -L, --url-list FILENAME         Target URL list
  -u, --url TEXT                  Target URL, option is mutually exclusive
                                  with url_list  [required]

  -l, --logs DIRECTORY            Destination directory for the logs
  --http-method [head|get]        HTTP method: GET or HEAD  [default: get]
  --help                          Show this message and exit.
```

Features
--------
- Asynchronous
- Can simultaneously scan unlimited number of sites
- Keep-alive support
- HTTP and SOCKS proxy support
- User agent randomization

Screenshot
--------
<p align="center">
        <img align="center" src="https://raw.githubusercontent.com/enemy-submarine/pidrila/main/Pidrila.png">
</p>

Usage examples
--------
Scan single clearweb site
```
 python3 ./pidrila.py -u http://silenthouse.yoba -M 128
```

Scan single onion site
```
 python3 ./pidrila.py -u http://zqktlwi4fecvo6ro.onion -m 16 -M 16 --proxy=socks5h://127.0.0.1:9050
```

Fast batch scan with custom User-Agent
```
python3 ./pidrila.py -m 2048 -L darkweb_sites_list.txt --user-agent "Pantusha/2.0 (4.2BSD)"
```

License
-------
License: GNU General Public License, version 2
