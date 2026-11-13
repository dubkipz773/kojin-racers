!function (w, d, t) {
  w.TiktokAnalyticsObject = t;
  var ttq = w[t] = w[t] || [];
  ttq.methods = ["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie"];
  ttq.setAndDefer = function(t, e) {
    t[e] = function() {
      t.push([e].concat(Array.prototype.slice.call(arguments, 0)));
    };
  };
  for (var i = 0; i < ttq.methods.length; i++) ttq.setAndDefer(ttq, ttq.methods[i]);
  ttq.instance = function(t) {
    for (var e = ttq._i[t] || [], n = 0; n < ttq.methods.length; n++) ttq.setAndDefer(e, ttq.methods[n]);
    return e;
  };
  ttq.load = function(e, n) {
    var i = "https://analytics.tiktok.com/i18n/pixel/events.js";
    ttq._i = ttq._i || {};
    ttq._i[e] = [];
    ttq._i[e]._u = i;
    ttq._t = ttq._t || {};
    ttq._t[e] = +new Date;
    ttq._o = ttq._o || {};
    ttq._o[e] = n || {};
    var o = document.createElement("script");
    o.type = "text/javascript";
    o.async = true;
    o.src = i + "?sdkid=" + e + "&lib=" + t;
    var a = document.getElementsByTagName("script")[0];
    a.parentNode.insertBefore(o, a);
  };
  ttq.load('7530775888124952593');
}(window, document, 'ttq');

analytics.subscribe("page_viewed", (event) => {
  ttq.page();
});

analytics.subscribe("product_viewed", (event) => {
  ttq.track('ViewContent', {
    content_id: String(event.data?.productVariant?.id || ''),
    content_name: event.data?.productVariant?.title,
    content_type: 'product',
    currency: event.data?.productVariant?.price?.currencyCode,
    value: Number(event.data?.productVariant?.price?.amount),
  });
});

analytics.subscribe("search_submitted", (event) => {
  ttq.track('Search', {
    query: event.data?.searchResult?.query,
    search_string: event.data?.searchResult?.query,
  });
});

analytics.subscribe("product_added_to_cart", (event) => {
  const variant = event.data?.cartLine?.merchandise?.productVariant;
  const qty = event.data?.cartLine?.quantity || 1;
  const price = Number(variant?.price?.amount);
  ttq.track('AddToCart', {
    contents: [{
      content_id: String(variant?.id || ''),
      content_name: variant?.title,
      quantity: qty,
      price: price,
    }],
    content_type: 'product',
    currency: variant?.price?.currencyCode,
    value: price * qty,
  });
});

analytics.subscribe("payment_info_submitted", (event) => {
  ttq.track('AddPaymentInfo');
});

analytics.subscribe("checkout_started", (event) => {
  ttq.track('InitiateCheckout', {
    currency: event.data?.checkout?.currencyCode,
    value: Number(event.data?.checkout?.totalPrice?.amount),
  });
});

analytics.subscribe("checkout_completed", (event) => {
  ttq.track('Purchase', {
    content_type: 'product',
    currency: event.data?.checkout?.currencyCode,
    value: Number(event.data?.checkout?.totalPrice?.amount),
  });
});
