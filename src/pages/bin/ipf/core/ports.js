const net = require("net")

const common = [80, 443, 22, 21, 3389]

exports.scanPorts = (host) => {
  return new Promise((resolve) => {
    const open = []
    let done = 0

    common.forEach(port => {
      const socket = new net.Socket()

      socket.setTimeout(500)

      socket.on("connect", () => {
        open.push(port)
        socket.destroy()
      })

      socket.on("timeout", () => socket.destroy())
      socket.on("error", () => {})

      socket.on("close", () => {
        done++
        if (done === common.length) resolve(open)
      })

      socket.connect(port, host)
    })
  })
}