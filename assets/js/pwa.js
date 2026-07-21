if('serviceWorker'in navigator)addEventListener('load',()=>navigator.serviceWorker.register('/service-worker.js').catch(()=>{}));
