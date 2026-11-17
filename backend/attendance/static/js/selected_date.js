document.getElementById('id_date_stamp').addEventListener('change', function() {
  const selectedDate = this.value;

  fetch(`/clock/?id_date_stamp=${selectedDate}`)
    .then(response => response.text())
    .then(data => {
      if (data) {
        document.getElementById('id_location').value = data.location;
        document.getElementById('id_break_time').value = data.break_time;
      }
    })
    .catch(error => console.error(error));
});
