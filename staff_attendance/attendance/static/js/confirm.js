document.querySelector('form').addEventListener('submit', function(event) {
  event.preventDefault();

  const userConfirmed = confirm('Are you sure you want to submit this request?');

  if (userConfirmed) {
    this.submit();
  } else {
    console.log('Submission canceled.');
  }
});
