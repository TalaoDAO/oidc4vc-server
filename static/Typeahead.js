// Constructing the suggestion engine
var ind = new Bloodhound({
  datumTokenizer: Bloodhound.tokenizers.obj.whitespace("name"),
  queryTokenizer: Bloodhound.tokenizers.whitespace,
  identify: function(obj) {
    return obj.username;
  },
  remote: {url : "/prefetch?q=%QUERY", wildcard: '%QUERY'} //can be heavy on the db
});
ind.initialize();
// Initializing the typeahead
$('#typeaheadElement').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
}, {
  name: 'ind',
  displayKey: "username",
  source: ind.ttAdapter(),
  templates: {
    empty: [
      '<div class="empty-message">',
      'No other suggestion found',
      '</div>'
    ].join('\n'),
    suggestion: function(item) {
      return "<p style='padding:6px'><b>" + item.name + "</b> - Username: " + item.name + "</p>";
    }
  }
});

// Initializing the typeahead
$('#typeaheadElementSM').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
}, {
  name: 'ind',
  displayKey: "username",
  source: ind.ttAdapter(),
  templates: {
    empty: [
      '<div class="empty-message">',
      'No other suggestion found',
      '</div>'
    ].join('\n'),
    suggestion: function(item) {
      return "<p style='padding:6px'><b>" + item.name + "</b> - Username: " + item.name + "</p>";
    }
  }
});
