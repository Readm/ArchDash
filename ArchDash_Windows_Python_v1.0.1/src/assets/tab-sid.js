// 每个浏览器标签生成唯一 _sid 并写入 URL
(function() {
  function hasSid() {
    return new URL(window.location.href).searchParams.has('_sid');
  }
  if (!hasSid()) {
    const url = new URL(window.location.href);
    url.searchParams.set('_sid', (self.crypto||window.crypto).randomUUID());
    // 使用 replace 避免产生后退记录
    window.location.replace(url.toString());
  }
})(); 