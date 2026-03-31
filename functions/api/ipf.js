import { json } from '@astrojs/cloudflare';
import fs from 'fs-extra';
import path from 'path';
import archiver from 'archiver';

const ROOT = new URL('../../public/', import.meta.url);

const FILES = [
  "bin/ipf/setPATH.bat",
  "bin/ipf/README.md",
  "bin/ipf/package.json",
  "bin/ipf/package-lock.json",
  "bin/ipf/license.txt",
  "bin/ipf/dist/ipf.exe",
  "bin/ipf/core/vpn.js",
  "bin/ipf/core/ports.js",
  "bin/ipf/core/ping.js",
  "bin/ipf/core/machine.js",
  "bin/ipf/core/logger.js",
  "bin/ipf/core/geo.js",
  "bin/ipf/core/dns.js",
  "bin/ipf/config/config.json",
  "bin/ipf/bin/ipf.js"
];

export async function GET({ url }) {
  const info = url.searchParams.get('info');
  const download = url.searchParams.get('download');

  if (info !== null) {
    const readme = {
      name: "IPF CLI",
      description: "Command-line tool for IP info, logging, and Discord webhook reporting.",
      features: [
        "Lookup IP geolocation, ISP, timezone, and Google Maps link",
        "View local PC network info (ipf -m)",
        "Save logs to Documents folder (ipf -l)",
        "Send IP info via Discord webhook (ipf -s {webhook} {ip})",
        "Portable CLI with setup batch for global PATH"
      ],
      usage: [
        "https://cdn-kjs.pages.dev/bin/ipf/dist/ipf.exe <ip>",
        "https://cdn-kjs.pages.dev/bin/ipf/dist/ipf.exe -m",
        "https://cdn-kjs.pages.dev/bin/ipf/dist/ipf.exe -l <ip>",
        "https://cdn-kjs.pages.dev/bin/ipf/dist/ipf.exe -s <webhook> <ip>"
      ]
    };
    return json(readme);
  }

  if (download !== null) {
    const archive = archiver('zip', { zlib: { level: 9 } });

    const headers = new Headers();
    headers.set('Content-Type', 'application/zip');
    headers.set('Content-Disposition', 'attachment; filename="ipf_files.zip"');

    const readable = new Response(archive, { headers });

    for (const file of FILES) {
      const filePath = path.join(ROOT.pathname, file);
      if (await fs.pathExists(filePath)) {
        archive.file(filePath, { name: file });
      }
    }

    archive.finalize();
    return readable;
  }

  return json({ error: "Invalid query. Use ?info or ?download" });
}