const form = document.getElementById('contact-form');
const status = document.getElementById('form-status');

if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    status.textContent = 'Sending message...';
    try {
      const response = await fetch('http://localhost:8080/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error('Unable to send message');
      }

      form.reset();
      status.textContent = 'Message sent successfully. Thank you!';
    } catch (error) {
      status.textContent = 'The API is not available yet. Please contact me directly by email.';
    }
  });
}
