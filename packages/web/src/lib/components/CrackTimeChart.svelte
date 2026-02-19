<script lang="ts">
	import { onMount } from 'svelte';
	import { Chart, BarController, CategoryScale, LogarithmicScale, BarElement, Tooltip, Legend } from 'chart.js';
	import type { EstimateResponse } from '$lib/api/client';
	import { RATING_COLORS } from '$lib/utils/format';

	Chart.register(BarController, CategoryScale, LogarithmicScale, BarElement, Tooltip, Legend);

	let { results, labelKey = 'hash_algorithm' }: { results: EstimateResponse[]; labelKey?: string } = $props();
	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;

	function buildChart() {
		if (chart) chart.destroy();
		if (!canvas || results.length === 0) return;

		const labels = results.map((r) => (r as Record<string, unknown>)[labelKey] as string);
		const data = results.map((r) => (r.crack_time_seconds ?? 1e30));
		const colors = results.map((r) => RATING_COLORS[r.rating] ?? '#6b7280');

		chart = new Chart(canvas, {
			type: 'bar',
			data: {
				labels,
				datasets: [
					{
						label: 'Crack Time (seconds)',
						data,
						backgroundColor: colors,
						borderRadius: 4
					}
				]
			},
			options: {
				indexAxis: 'y',
				responsive: true,
				maintainAspectRatio: false,
				scales: {
					x: {
						type: 'logarithmic',
						title: { display: true, text: 'Seconds (log scale)' }
					}
				},
				plugins: {
					legend: { display: false },
					tooltip: {
						callbacks: {
							label: (ctx) => {
								const r = results[ctx.dataIndex];
								return `${r.crack_time_display} (${r.rating_label})`;
							}
						}
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
		// Re-render when results change
		if (results && canvas) buildChart();
	});
</script>

<div class="h-64">
	<canvas bind:this={canvas}></canvas>
</div>
