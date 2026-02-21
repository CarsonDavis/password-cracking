<script lang="ts">
	import { onMount } from 'svelte';
	import { Chart, DoughnutController, ArcElement, Tooltip, Legend } from 'chart.js';
	import { RATING_COLORS } from '$lib/utils/format';

	Chart.register(DoughnutController, ArcElement, Tooltip, Legend);

	let { distribution, labels }: { distribution: Record<string | number, number>; labels?: Record<string | number, string> } = $props();
	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;

	const RATING_LABELS: Record<number, string> = {
		0: 'Critical',
		1: 'Weak',
		2: 'Fair',
		3: 'Strong',
		4: 'Very Strong'
	};

	function buildChart() {
		if (chart) chart.destroy();
		if (!canvas) return;

		const entries = Object.entries(distribution);
		const chartLabels = entries.map(([k]) => labels?.[k] ?? RATING_LABELS[Number(k)] ?? k);
		const data = entries.map(([, v]) => v);
		const colors = entries.map(([k]) => RATING_COLORS[Number(k)] ?? '#6b7280');

		chart = new Chart(canvas, {
			type: 'doughnut',
			data: {
				labels: chartLabels,
				datasets: [{ data, backgroundColor: colors }]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						position: 'right',
						labels: { color: '#e8e6e3' }
					}
				}
			}
		});
	}

	onMount(() => {
		buildChart();
		return () => chart?.destroy();
	});

	$effect(() => {
		if (distribution && canvas) buildChart();
	});
</script>

<div class="h-48">
	<canvas bind:this={canvas}></canvas>
</div>
