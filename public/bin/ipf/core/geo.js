const axios = require("axios")

exports.getGeo = async (ip) => {
  const res = await axios.get(`http://ip-api.com/json/${ip}`)
  return res.data
}