export async function onRequest(context) {
  const url = new URL(context.request.url);
  const action = url.searchParams.get("action");
  const file = url.searchParams.get("file");
  const type = url.searchParams.get("type");

  const files = [
    "dart.py",
    "pc-game.py",
    "pc-gameinthemaking.py",
    "puzzle.py",
    "README.txt",
    "run_all_games.bat"
  ];

  if (action === "view") {
    const data = {};
    for (const f of files) {
      try {
        const res = await fetch(new URL(`/bin/${f}`, context.request.url));
        if (!res.ok) {
          data[f] = `Error: ${res.status} ${res.statusText}`;
        } else {
          data[f] = await res.text();
        }
      } catch (err) {
        data[f] = `Error fetching file: ${err.message}`;
      }
    }

    return new Response(JSON.stringify(data, null, 2), {
      headers: { "Content-Type": "application/json" }
    });
  }

  if (action === "download" && file) {
    if (!files.includes(file)) {
      return new Response("File not found", { status: 404 });
    }

    try {
      const res = await fetch(new URL(`/bin/${file}`, context.request.url));
      if (!res.ok) return new Response("File not found", { status: 404 });

      const content = await res.arrayBuffer();

      return new Response(content, {
        headers: {
          "Content-Type": "application/octet-stream",
          "Content-Disposition": `attachment; filename="${file}"`
        }
      });
    } catch (err) {
      return new Response(`Error fetching file: ${err.message}`, { status: 500 });
    }
  }

  if (action === "download" && type === "zip") {
    return new Response(
      "ZIP not supported yet — tell me and I’ll add it properly",
      { status: 501 }
    );
  }

  return new Response("Invalid request", { status: 400 });
}