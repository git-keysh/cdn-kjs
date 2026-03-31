const fs = require("fs")
const os = require("os")
const path = require("path")

const file = path.join(os.homedir(), "Documents", "ipf_logs.json")

exports.saveLog = (data) => {
  let logs = []
  if (fs.existsSync(file)) logs = JSON.parse(fs.readFileSync(file))
  logs.push(data)
  fs.writeFileSync(file, JSON.stringify(logs, null, 2))
}

exports.readLogs = () => {
  if (!fs.existsSync(file)) return "No logs"
  return fs.readFileSync(file, "utf-8")
}

exports.clearLogs = () => {
  fs.writeFileSync(file, "[]")
}