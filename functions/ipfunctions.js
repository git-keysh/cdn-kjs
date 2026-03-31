import fs from 'fs';
import path from 'path';

const ZIP_PATH = path.join(process.cwd(), 'public', 'bin', 'ipf.zip');

export async function GET({ url }) {
  const queryParams = new URL(url).searchParams;
  const action = queryParams.get('ipfunctions');

  if (action === 'info') {
    const info = {
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

    return new Response(JSON.stringify(info), {
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }

  if (action === 'download') {
    if (!fs.existsSync(ZIP_PATH)) {
      return new Response(JSON.stringify({ error: "Zip file not found." }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const fileBuffer = fs.readFileSync(ZIP_PATH);
    return new Response(fileBuffer, {
      headers: {
        'Content-Type': 'application/zip',
        'Content-Disposition': 'attachment; filename="ipf.zip"'
      }
    });
  }

  return new Response(JSON.stringify({ error: "Invalid action. Use ?ipfunctions=info or ?ipfunctions=download" }), {
    status: 400,
    headers: { 'Content-Type': 'application/json' }
  });
}