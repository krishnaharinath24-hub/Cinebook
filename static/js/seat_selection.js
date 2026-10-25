// CineBook Interactive Cinema Seat Selection Logic
document.addEventListener('DOMContentLoaded', function () {
  const seatButtons = document.querySelectorAll('.seat-box.available');
  const selectedSeatsChips = document.getElementById('selectedSeatsChips');
  const selectedSeatsCount = document.getElementById('selectedSeatsCount');
  const ticketSubtotalEl = document.getElementById('ticketSubtotal');
  const convenienceFeeEl = document.getElementById('convenienceFee');
  const totalAmountEl = document.getElementById('totalAmount');
  const checkoutBtn = document.getElementById('proceedCheckoutBtn');
  const hiddenSeatIdsInput = document.getElementById('hiddenSeatIds');
  const seatCountNotice = document.getElementById('seatCountNotice');

  // Load convenience fee per ticket from data attribute or default to 30.00
  const feePerTicket = parseFloat(document.getElementById('bookingConfig')?.dataset?.convenienceFee || 30.0);
  const maxSeatsAllowed = 10;

  // Selected seats state: array of { id, code, tier, price }
  let selectedSeats = [];

  seatButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const seatId = parseInt(this.dataset.seatId);
      const seatCode = this.dataset.seatCode;
      const seatTier = this.dataset.seatTier;
      const seatPrice = parseFloat(this.dataset.seatPrice);

      const existingIndex = selectedSeats.findIndex(s => s.id === seatId);

      if (existingIndex > -1) {
        // Deselect seat
        selectedSeats.splice(existingIndex, 1);
        this.classList.remove('selected');
        this.setAttribute('aria-selected', 'false');
      } else {
        // Check maximum capacity
        if (selectedSeats.length >= maxSeatsAllowed) {
          alert(`You can select a maximum of ${maxSeatsAllowed} seats per booking.`);
          return;
        }
        // Select seat
        selectedSeats.push({
          id: seatId,
          code: seatCode,
          tier: seatTier,
          price: seatPrice
        });
        this.classList.add('selected');
        this.setAttribute('aria-selected', 'true');
      }

      updateSummaryUI();
    });
  });

  function updateSummaryUI() {
    const count = selectedSeats.length;

    // 1. Update Chips & Hidden Input
    if (count === 0) {
      selectedSeatsChips.innerHTML = '<span class="text-dim" style="font-size: 0.85rem; color: #6b7280;">No seats selected yet. Click seats to select.</span>';
      hiddenSeatIdsInput.value = '';
      checkoutBtn.disabled = true;
      checkoutBtn.style.opacity = '0.5';
      checkoutBtn.style.cursor = 'not-allowed';
      if (seatCountNotice) seatCountNotice.textContent = 'Select seats on the map to begin.';
    } else {
      selectedSeatsChips.innerHTML = selectedSeats.map(s => `
        <span class="seat-chip" title="${s.tier} - ₹${s.price.toFixed(2)}">
          ${s.code}
        </span>
      `).join('');

      hiddenSeatIdsInput.value = selectedSeats.map(s => s.id).join(',');
      checkoutBtn.disabled = false;
      checkoutBtn.style.opacity = '1';
      checkoutBtn.style.cursor = 'pointer';
      if (seatCountNotice) seatCountNotice.textContent = `${count} seat${count > 1 ? 's' : ''} selected.`;
    }

    // 2. Calculate Prices
    let subtotal = 0;
    selectedSeats.forEach(s => {
      subtotal += s.price;
    });

    const convenienceFee = count > 0 ? (count * feePerTicket) : 0;
    const totalAmount = subtotal + convenienceFee;

    // 3. Update DOM Labels
    if (selectedSeatsCount) selectedSeatsCount.textContent = count;
    if (ticketSubtotalEl) ticketSubtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
    if (convenienceFeeEl) convenienceFeeEl.textContent = `₹${convenienceFee.toFixed(2)}`;
    if (totalAmountEl) totalAmountEl.textContent = `₹${totalAmount.toFixed(2)}`;
  }

  // Initialize state
  updateSummaryUI();
});
