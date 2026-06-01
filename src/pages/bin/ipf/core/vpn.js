const axios = require("axios")

exports.checkVPN = async (ip) => {
  const res = await axios.get(`https://proxycheck.io/v2/${ip}?vpn=1`)
  const data = res.data[ip]

  return {
    vpn: data.proxy === "yes" ? "Yes" : "No",
    proxy: data.proxy === "yes" ? "Yes" : "No"
  }
}