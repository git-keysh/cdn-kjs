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

    function zipFiles(fileMap) {
      let zipParts = []
      let offset = 0
      const centralDirectory = []

      for (const name in fileMap) {
        const content = fileMap[name]
        const contentBytes = typeof content === "string" ? strToUint8(content) : new Uint8Array(content)
        const localHeader = new Uint8Array([
          0x50,0x4b,0x03,0x04,
          20,0, 0,0, 0,0, 0,0,
          0,0,0,0,
          contentBytes.length & 0xff,
          (contentBytes.length >> 8) & 0xff,
          (contentBytes.length >>16)&0xff,
          (contentBytes.length >>24)&0xff,
          contentBytes.length & 0xff,
          (contentBytes.length >> 8) & 0xff,
          (contentBytes.length >>16)&0xff,
          (contentBytes.length >>24)&0xff,
          name.length & 0xff,
          (name.length >> 8) & 0xff
        ])
        zipParts.push(localHeader, strToUint8(name), contentBytes)
        centralDirectory.push({ name, offset, size: contentBytes.length })
        offset += localHeader.length + name.length + contentBytes.length
      }

      let cdStart = offset
      for (const file of centralDirectory) {
        const cdHeader = new Uint8Array([
          0x50,0x4b,0x01,0x02,
          20,0, 20,0, 0,0,0,0, 0,0,0,0,
          file.size &0xff,(file.size>>8)&0xff,(file.size>>16)&0xff,(file.size>>24)&0xff,
          file.size &0xff,(file.size>>8)&0xff,(file.size>>16)&0xff,(file.size>>24)&0xff,
          file.name.length &0xff,(file.name.length>>8)&0xff,0,0,0,0,0,0,0,0,
          file.offset &0xff,(file.offset>>8)&0xff,(file.offset>>16)&0xff,(file.offset>>24)&0xff
        ])
        zipParts.push(cdHeader, strToUint8(file.name))
        offset += cdHeader.length + file.name.length
      }

      const eocd = new Uint8Array([
        0x50,0x4b,0x05,0x06,
        0,0, 0,0,
        centralDirectory.length &0xff,(centralDirectory.length>>8)&0xff,
        centralDirectory.length &0xff,(centralDirectory.length>>8)&0xff,
        offset - cdStart &0xff,((offset - cdStart)>>8)&0xff,((offset - cdStart)>>16)&0xff,((offset - cdStart)>>24)&0xff,
        0,0
      ])
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