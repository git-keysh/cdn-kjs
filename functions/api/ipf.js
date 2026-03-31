import { json } from '@astrojs/cloudflare';
import fetch from 'node-fetch';
import archiver from 'archiver';

const BASE = 'https://cdn-kjs.pages.dev/';

export async function GET({ url }) {
  const info = url.searchParams.get('info');
  const download = url.searchParams.get('download');

  if (info !== null) {
    return json({
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
        `${BASE}bin/ipf/dist/ipf.exe <ip>`,
        `${BASE}bin/ipf/dist/ipf.exe -m`,
        `${BASE}bin/ipf/dist/ipf.exe -l <ip>`,
        `${BASE}bin/ipf/dist/ipf.exe -s <webhook> <ip>`
      ]
    });
  }

  if (download !== null) {
    const res = await fetch(`${BASE}bin/ipf/files.json`);
    const files = await res.json();

    const archive = archiver('zip', { zlib: { level: 9 } });
    const headers = new Headers();
    headers.set('Content-Type', 'application/zip');
    headers.set('Content-Disposition', 'attachment; filename="ipf_files.zip"');

    const stream = new ReadableStream({
      async start(controller) {
        archive.on('data', chunk => controller.enqueue(chunk));
        archive.on('end', () => controller.close());
        archive.on('error', err => controller.error(err));

        for (const file of files) {
          const fileRes = await fetch(BASE + file.replace(/^public\//, ''));
          const buffer = Buffer.from(await fileRes.arrayBuffer());
          archive.append(buffer, { name: file.replace(/^public\//, '') });
        }

        archive.finalize();
      }
    });

    return new Response(stream, { headers });
  }

  return json({ error: "Invalid query. Use ?info or ?download" });
}