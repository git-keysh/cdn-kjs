# IPF CLI

🌐 **IPF** is a command-line tool for fetching detailed IP information, geolocation, PC network info, logging, and Discord webhook reporting.

---

## Features

- Lookup IP geolocation, ISP, timezone, and Google Maps link  
- View local PC network info (`ipf -m`)  
- Save logs to the Documents folder (`ipf -l`)  
- Send IP info via Discord webhook (`ipf -s {webhook} {ip}`)  
- Fully portable CLI with a setup batch for global PATH  
- Works on any Windows PC  

---

## Installation

1. Download the repository.  
2. Run `dist\ipf.exe` to test the CLI.  
3. To make it global, run the `setPATH.bat` batch file included:  

```bat
setPATH.bat
````

4. Restart CMD or PowerShell.

Now you can run `ipf` from anywhere.

---

## Usage

```bash
ipf 8.8.8.8          # Lookup IP information
ipf -m                # Show PC network info
ipf -l 8.8.8.8       # Save IP info to logs in Documents
ipf -s <webhook> 8.8.8.8  # Send IP info to Discord webhook
```

---

## Discord Embed Format

When using `-s`, IP info is sent as a rich embed:

```json
{
  "embeds": [
    {
      "title": "🌐 Visitor Detection",
      "color": 5793266,
      "fields": [
        { "name": "🌐 IP Address", "value": "8.8.8.8", "inline": true },
        { "name": "📍 Location", "value": "Ashburn, United States, 📍 39.03, -77.5", "inline": true },
        { "name": "🏢 ISP", "value": "Google LLC", "inline": true }
      ],
      "footer": { "text": "Detection Time" },
      "timestamp": "2026-03-31T02:07:45.254Z"
    }
  ]
}
```

---

## License

**FAVnC License** (sample)
Copyright (c) 2025 Pat Williams (FAVnC)

Permission is granted to the licensee only as set forth in the purchase agreement. Redistribution or resale is strictly prohibited unless expressly authorized in writing by Pat Williams. All rights reserved.

Violation of license terms results in immediate termination of rights. FAVnC may pursue injunctive relief and damages. Upon termination, the licensee must stop using the materials and delete all copies unless otherwise required by law for record-keeping.

---

## Notes

* Make sure `config.json` is valid before running
* Batch setup (`setPATH.bat`) must be run once per PC to use `ipf` globally
* Compatible with Windows 10/11
