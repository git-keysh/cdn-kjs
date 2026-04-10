export async function onRequest(context) {
  const { request } = context;
  
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  try {
    const { name, email, project, message } = await request.json();
    
    if (!name || !email) {
      return new Response(JSON.stringify({ error: 'Name and email are required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const webhookURL = context.env.DISCORD_WEBHOOK_URL;
    
    if (!webhookURL) {
      console.error('Missing DISCORD_WEBHOOK_URL environment variable');
      return new Response(JSON.stringify({ error: 'Service configuration error' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const payload = {
      content: `**New inquiry from Real Media Marketing**\n**Name:** ${name}\n**Email:** ${email}\n**Project type:** ${project || 'Not specified'}\n**Message:** ${message || 'No message provided'}`
    };

    const discordResponse = await fetch(webhookURL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!discordResponse.ok) {
      throw new Error(`Discord webhook failed: ${discordResponse.status}`);
    }

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    console.error('Webhook error:', error);
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}