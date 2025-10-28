const ball = document.getElementById('rainbowBall');
const colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet'];
let colorIndex = 0;
let direction = 1;
let position = 20;

function animate() {
  // Bounce effect
  if (position >= 60 || position <= 20) direction *= -1;
  position += direction * 2;
  ball.style.bottom = position + 'px';

  // Cycle through rainbow colors
  colorIndex = (colorIndex + 1) % colors.length;
  ball.style.backgroundColor = colors[colorIndex];

  requestAnimationFrame(animate);
}

animate();