import JSZip from "jszip"

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
    const zip = new JSZip()
    for (const f of files) {
      const res = await fetch(new URL(`/bin/${f}`, context.request.url))
      if (res.ok) {
        const content = await res.arrayBuffer()
        zip.file(f, content)
      }
    }
    const zipContent = await zip.generateAsync({ type: "uint8array" })
    return new Response(zipContent, {
      headers: {
        "Content-Type": "application/zip",
        "Content-Disposition": `attachment; filename="all_files.zip"`
      }
    })
  }

  return new Response("Invalid request", { status: 400 })
}