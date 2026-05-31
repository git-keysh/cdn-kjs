const MYMEMORY = "https://api.mymemory.translated.net/get";

export async function onRequestGet(context) {
  const { searchParams } = new URL(context.request.url);

  const toSpanish = searchParams.get("spanish"); // EN → ES
  const toEnglish = searchParams.get("english"); // ES → EN

  if (!toSpanish && !toEnglish) {
    return Response.json(
      { error: "Provide either ?spanish=<english text> or ?english=<spanish text>" },
      { status: 400 }
    );
  }

  if (toSpanish && toEnglish) {
    return Response.json(
      { error: "Provide only one parameter at a time" },
      { status: 400 }
    );
  }

  const text    = toSpanish ?? toEnglish;
  const langPair = toSpanish ? "en|es" : "es|en";
  const from    = toSpanish ? "en" : "es";
  const to      = toSpanish ? "es" : "en";

  if (text.length > 500) {
    return Response.json(
      { error: "Text too long. Max 500 characters." },
      { status: 400 }
    );
  }

  let data;
  try {
    const res = await fetch(
      `${MYMEMORY}?q=${encodeURIComponent(text)}&langpair=${langPair}`
    );

    if (!res.ok) throw new Error(`MyMemory returned ${res.status}`);
    data = await res.json();
  } catch (err) {
    return Response.json(
      { error: "Translation service unavailable", details: String(err) },
      { status: 502 }
    );
  }

  if (data.responseStatus !== 200) {
    return Response.json(
      { error: data.responseDetails ?? "Translation failed" },
      { status: 422 }
    );
  }

  return Response.json({
    input: text,
    output: data.responseData.translatedText,
    from,
    to,
    match: data.responseData.match, // confidence 0–1
  }, {
    headers: { "Access-Control-Allow-Origin": "*" }
  });
}