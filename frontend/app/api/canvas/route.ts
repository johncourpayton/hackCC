export async function GET(request: Request) {
  try {
    const backendUrl = 'http://localhost:5000/api/assignments';
    const response = await fetch(backendUrl);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Backend error: ${response.status} - ${errorText}`);
      return new Response(JSON.stringify({ error: `Backend responded with status ${response.status}: ${errorText}` }), {
        status: response.status,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    }

    const assignments = await response.json();

    return new Response(JSON.stringify(assignments), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error: any) {
    console.error(`Failed to fetch Canvas assignments from backend: ${error.message}`);
    return new Response(JSON.stringify({ error: `Failed to connect to backend: ${error.message}` }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
}
