const chalk = require("chalk")
const boxen = require("boxen")
const dns = require("dns").promises
const fs = require("fs")
const path = require("path")

const { getGeo } = require("../core/geo")
const { getMachine } = require("../core/machine")
const { reverseDNS } = require("../core/dns")
const { scanPorts } = require("../core/ports")
const { checkVPN } = require("../core/vpn")
const { pingHost } = require("../core/ping")
const { saveLog, readLogs, clearLogs } = require("../core/logger")

const configPath = path.join(__dirname, "../config/config.json")

const args = process.argv.slice(2)

function loadConfig() {
  if (!fs.existsSync(configPath)) return {}
  return JSON.parse(fs.readFileSync(configPath))
}

function saveConfig(cfg) {
  fs.writeFileSync(configPath, JSON.stringify(cfg, null, 2))
}

async function resolveTarget(target) {
  if (target === "me") {
    const axios = require("axios")
    const res = await axios.get("https://api.ipify.org?format=json")
    return res.data.ip
  }

  try {
    const res = await dns.lookup(target)
    return res.address
  } catch {
    return target
  }
}

function renderBox(data) {
  return boxen(data, {
    padding: 1,
    borderStyle: "round"
  })
}

async function run() {
  if (!args.length) {
    console.log("ipf <ip|domain|me> [options]")
    return
  }

  if (args[0] === "-m") {
    console.log(getMachine())
    return
  }

  if (args[0] === "-l") {
    if (args[1] === "view") return console.log(readLogs())
    if (args[1] === "clear") return clearLogs()
    return console.log("Use: -l view | clear")
  }

  if (args[0] === "--set-webhook") {
    const cfg = loadConfig()
    cfg.webhook = args[1]
    saveConfig(cfg)
    console.log("Webhook saved")
    return
  }

  const target = await resolveTarget(args[0])

  const geo = await getGeo(target)
  const rdns = args.includes("--rdns") ? await reverseDNS(target) : null
  const vpn = args.includes("--full") || args.includes("--recon") ? await checkVPN(target) : null
  const ports = args.includes("--ports") || args.includes("--recon") ? await scanPorts(target) : null
  const ping = args.includes("--ping") || args.includes("--recon") ? await pingHost(target) : null

  const map = `https://www.google.com/maps?q=${geo.lat},${geo.lon}`

  const output = `
🌐 IP: ${geo.query}
📍 ${geo.city}, ${geo.country}
🏢 ${geo.isp}
🧭 ${geo.timezone}
🗺️ ${map}
${rdns ? `🔁 RDNS: ${rdns}` : ""}
${vpn ? `🔒 VPN: ${vpn.vpn} | Proxy: ${vpn.proxy}` : ""}
${ports ? `📡 Ports: ${ports.join(", ")}` : ""}
${ping ? `⚡ Ping: ${ping}ms` : ""}
`

  console.log(renderBox(chalk.cyan(output)))

  saveLog({
    ip: geo.query,
    location: geo.city,
    isp: geo.isp,
    time: new Date().toISOString()
  })

  const cfg = loadConfig()
  if (cfg.webhook) {
    const axios = require("axios")

    await axios.post(cfg.webhook, {
      embeds: [{
        title: "🌐 IPF Recon",
        color: 5793266,
        fields: [
          { name: "IP", value: geo.query, inline: true },
          { name: "Location", value: `${geo.city}, ${geo.country}`, inline: true },
          { name: "ISP", value: geo.isp, inline: true },
          { name: "VPN", value: vpn ? vpn.vpn : "N/A", inline: true },
          { name: "Ping", value: ping ? `${ping}ms` : "N/A", inline: true }
        ],
        timestamp: new Date().toISOString()
      }]
    })
  }
}

run()