export async function onRequest(context) {
  const url = new URL(context.request.url)
  const action = url.searchParams.get("action")
  const file = url.searchParams.get("file")
  const type = url.searchParams.get("type")

  const files = [
    "dart.py",
    "pc-game.py",
    "pc-gameinthemaking.py",
    "puzzle.py",
    "README.txt",
    "run_all_games.bat"
  ]

  if (action === "view") {
    const data = {}
    for (const f of files) {
      const res = await fetch(new URL(`/bin/${f}`, context.request.url))
      data[f] = res.ok ? await res.text() : `Error: ${res.status}`
    }
    return new Response(JSON.stringify(data, null, 2), {
      headers: { "Content-Type": "application/json" }
    })
  }

  if (action === "download" && file && file !== "zip") {
    if (!files.includes(file)) return new Response("File not found", { status: 404 })
    const res = await fetch(new URL(`/bin/${file}`, context.request.url))
    if (!res.ok) return new Response("File not found", { status: 404 })
    const content = await res.arrayBuffer()
    return new Response(content, {
      headers: {
        "Content-Type": "application/octet-stream",
        "Content-Disposition": `attachment; filename="${file}"`
      }
    })
  }

  if (action === "download" && type === "zip") {
    function strToUint8(str) {
      const buf = new Uint8Array(str.length)
      for (let i = 0; i < str.length; i++) buf[i] = str.charCodeAt(i)
      return buf
    }

    function crc32(buf) {
      let crc = -1
      for (let b of buf) {
        crc ^= b
        for (let k = 0; k < 8; k++) crc = (crc >>> 1) ^ (0xEDB88320 & -(crc & 1))
      }
      return (crc ^ -1) >>> 0
    }

    function zipFiles(fileMap) {
      let zipParts = []
      let centralDirectory = []
      let offset = 0

      for (const name in fileMap) {
        const contentBuf = new Uint8Array(fileMap[name])
        const cksum = crc32(contentBuf)
        const localHeader = new Uint8Array(30)
        const dv = new DataView(localHeader.buffer)
        dv.setUint32(0, 0x04034b50, true)
        dv.setUint16(4, 20, true)
        dv.setUint16(6, 0, true)
        dv.setUint16(8, 0, true)
        dv.setUint16(10, 0, true)
        dv.setUint32(14, cksum, true)
        dv.setUint32(18, contentBuf.length, true)
        dv.setUint32(22, contentBuf.length, true)
        dv.setUint16(26, name.length, true)
        dv.setUint16(28, 0, true)
        zipParts.push(localHeader, strToUint8(name), contentBuf)
        centralDirectory.push({ name, offset, size: contentBuf.length, cksum })
        offset += localHeader.length + name.length + contentBuf.length
      }

      let cdStart = offset
      for (const file of centralDirectory) {
        const cdHeader = new Uint8Array(46)
        const dv = new DataView(cdHeader.buffer)
        dv.setUint32(0, 0x02014b50, true)
        dv.setUint16(4, 20, true)
        dv.setUint16(6, 20, true)
        dv.setUint16(8, 0, true)
        dv.setUint16(10, 0, true)
        dv.setUint16(12, 0, true)
        dv.setUint32(16, file.cksum, true)
        dv.setUint32(20, file.size, true)
        dv.setUint32(24, file.size, true)
        dv.setUint16(28, file.name.length, true)
        dv.setUint16(30, 0, true)
        dv.setUint16(32, 0, true)
        dv.setUint16(34, 0, true)
        dv.setUint16(36, 0, true)
        dv.setUint32(38, file.offset, true)
        zipParts.push(cdHeader, strToUint8(file.name))
        offset += cdHeader.length + file.name.length
      }

      const eocd = new Uint8Array(22)
      const dv = new DataView(eocd.buffer)
      dv.setUint32(0, 0x06054b50, true)
      dv.setUint16(4, 0, true)
      dv.setUint16(6, 0, true)
      dv.setUint16(8, centralDirectory.length, true)
      dv.setUint16(10, centralDirectory.length, true)
      dv.setUint32(12, offset - cdStart, true)
      dv.setUint32(16, cdStart, true)
      dv.setUint16(20, 0, true)
      zipParts.push(eocd)

      return new Blob(zipParts, { type: "application/zip" })
    }

    const fileMap = {}
    for (const f of files) {
      const res = await fetch(new URL(`/bin/${f}`, context.request.url))
      if (res.ok) fileMap[f] = await res.arrayBuffer()
    }

    const zipBlob = zipFiles(fileMap)
    const arrBuf = await zipBlob.arrayBuffer()
    return new Response(arrBuf, {
      headers: {
        "Content-Type": "application/zip",
        "Content-Disposition": `attachment; filename="all_files.zip"`
      }
    })
  }

  return new Response("Invalid request", { status: 400 })
}