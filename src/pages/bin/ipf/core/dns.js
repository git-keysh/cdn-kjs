const dns = require("dns").promises

exports.reverseDNS = async (ip) => {
  try {
    const res = await dns.reverse(ip)
    return res[0] || "None"
  } catch {
    return "None"
  }
}