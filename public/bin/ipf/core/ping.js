const { exec } = require("child_process")

exports.pingHost = (ip) => {
  return new Promise((resolve) => {
    exec(`ping -n 1 ${ip}`, (err, stdout) => {
      const match = stdout.match(/time=(\d+)ms/)
      resolve(match ? match[1] : "N/A")
    })
  })
}