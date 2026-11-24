(function () {
  const mainSitePath = "/admin/main-site/";

  function isMainSiteLink(link) {
    if (!link || !link.href) {
      return false;
    }

    const url = new URL(link.href, window.location.origin);
    return url.origin === window.location.origin && url.pathname === mainSitePath;
  }

  document.addEventListener("click", function (event) {
    const link = event.target.closest("a");

    if (!isMainSiteLink(link)) {
      return;
    }

    event.preventDefault();
    window.location.replace(link.href);
  });

  window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
      window.location.reload();
    }
  });
})();
