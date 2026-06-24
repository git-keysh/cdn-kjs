const os = require("os")

exports.getMachine = () => {
  const nets = os.networkInterfaces()
  let out = ""

  for (const name in nets) {
    for (const net of nets[name]) {
      if (net.family === "IPv4" && !net.internal) {
        out += `${name}: ${net.address}\n`
      }
    }
  }

  return out
}