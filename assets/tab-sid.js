// 每个浏览器标签生成唯一 _sid 并写入 URL
(function() {
  // UUID v4 生成函数 (polyfill for crypto.randomUUID)
  function generateUUID() {
    // 首先尝试使用原生的 randomUUID
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    
    // 如果不支持，使用 polyfill
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0;
      var v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  
  function hasSid() {
    return new URL(window.location.href).searchParams.has('_sid');
  }
  
  if (!hasSid()) {
    const url = new URL(window.location.href);
    url.searchParams.set('_sid', generateUUID());
    // 使用 replace 避免产生后退记录
    window.location.replace(url.toString());
  }
})(); 