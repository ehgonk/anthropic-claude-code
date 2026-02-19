import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

export default function TestChart() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) {
      console.log('TestChart: No container');
      return;
    }

    console.log('TestChart: Creating chart...');
    const container = containerRef.current;

    // Log container dimensions
    const rect = container.getBoundingClientRect();
    console.log('TestChart: Container dimensions:', {
      width: rect.width,
      height: rect.height,
      clientWidth: container.clientWidth,
      clientHeight: container.clientHeight
    });

    const chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#2a2a2a' },
        horzLines: { color: '#2a2a2a' },
      },
    });

    console.log('TestChart: Chart created');

    const lineSeries = chart.addLineSeries({
      color: '#3b82f6',
      lineWidth: 2,
    });

    // Hardcoded test data - last 100 days
    const now = Date.now() / 1000;
    const testData = Array.from({ length: 100 }, (_, i) => ({
      time: (now - (100 - i) * 86400) as any,
      value: 100 + Math.sin(i / 10) * 20 + Math.random() * 10
    }));

    console.log('TestChart: Setting data, points:', testData.length);
    lineSeries.setData(testData);

    chart.timeScale().fitContent();
    console.log('TestChart: Done');

    return () => {
      console.log('TestChart: Cleanup');
      chart.remove();
    };
  }, []);

  return (
    <div className="w-full h-full bg-red-500/20 border-2 border-red-500">
      <div className="text-white p-2 text-xs">TestChart Container</div>
      <div
        ref={containerRef}
        className="w-full h-[300px] bg-blue-500/20"
      />
    </div>
  );
}
