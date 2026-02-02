export function randFloat(min, max) {
	return Math.random() * (max - min) + min;
}

export function randInt(min, max) {
	return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function lerp(start, end, amount) {
	return start + (end - start) * amount;
}

export function shuffle(array) {
	let currentIndex = array.length, randomIndex;

	while (currentIndex !== 0) {
		randomIndex = Math.floor(Math.random() * currentIndex);
		currentIndex--;
		[array[currentIndex], array[randomIndex]] = [array[randomIndex], array[currentIndex]];
	}

	return array;
}
