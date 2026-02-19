import { useEffect } from 'react';

export default function SimpleTest() {
  useEffect(() => {
    console.log('=== SimpleTest MOUNTED ===');
    console.log('Browser:', navigator.userAgent);
    console.log('Window size:', { width: window.innerWidth, height: window.innerHeight });

    return () => {
      console.log('=== SimpleTest UNMOUNTED ===');
    };
  }, []);

  return (
    <div className="w-full h-full p-4 bg-gradient-to-br from-purple-600 to-blue-600 flex flex-col items-center justify-center gap-4 text-white">
      <div className="text-4xl font-bold">✅ React Está Funcionando!</div>
      <div className="text-xl">Este é um teste simples sem bibliotecas externas</div>
      <div className="mt-4 p-4 bg-black/30 rounded-lg">
        <div className="text-sm">Abra o Console (F12) e procure por:</div>
        <div className="text-xs font-mono mt-2 text-yellow-300">
          === SimpleTest MOUNTED ===
        </div>
      </div>
    </div>
  );
}
