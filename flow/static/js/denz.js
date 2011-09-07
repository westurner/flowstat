//<![CDATA[
    /*
     * Config
     */

    //deniz_root = ""

    sparql_endpoint = '/sparql';
    force_result_limit = 100;
    initial_query = "SELECT ?g ?s ?p ?o WHERE { GRAPH ?g { ?s ?p ?o } }";
    title_prefix = "rdf browser";

    /*
     * Helper
     */

    jQuery.uuid4 = function () {
        bytes = []
        for (var i=0; i<16; i++) bytes.push(Math.floor(Math.random()*0x100).toString(16));
        return bytes.slice(0, 4).join('') + '-' + bytes.slice(4, 6).join('') + '-' + bytes.slice(6, 8).join('') + '-' + bytes.slice(8, 10).join('') + '-' + bytes.slice(10, 16).join('');
    };

    function render_term(term) {
        if (!term) {
            value = '';
        } else if (term.type == 'uri') {
            value = '<a href="#&lt;' + term.value + '&gt;">&lt;' + term.value + '&gt;</a>';
        } else if (term.type == 'typed-literal') {
            value = '"' + term.value + '"^^&lt;' + term.datatype + '&gt;';
        } else {
            value = '"' + term.value + '"';
        }
        return value;
    }

    /*
     * Offer SPARQL query console
     */
    // Limit results and provide "more..." button
    var limit_regex = /(LIMIT\s+)(\d+)([^\{\}<>]*)$/i;
    var offset_regex = /(OFFSET\s+)(\d+)([^\{\}<>]*)$/i;

    function load_table(data, user_query, query_str, insert_into) {
        // Mark-up header
        var header_ths = [];
        vars = data.head.vars;
        head = '<th>' + vars.join('</th><th>') + '</th>';
        // Mark-up rows
        var data_trs = [];
        $.each(data.results.bindings, function(i, row) {
            var tds = [];
            $.each(data.head.vars, function(i, element) {
                tds.push('<td>' + render_term(row[element]) + '</td>');
            });
            data_trs.push('<tr>' + tds.join('') + '</tr>');
        });
        rows = data_trs.join('');

        if (!insert_into) {
            id = $.uuid4();
            textarea = '<textarea id="'+id+'_querytxt"  style="width:80%; height: 40px;border:1px solid #f0f0f0">'+query_str+'</textarea> <a id="'+id+'_querybtn" href="#'+query_string+'">+</a>'; // # !!
            $('#' + id +' .result_container').html('<div id="' + id + '"><table class="resulttable"><thead><tr>'+textarea+'</tr><tr>' + head + '</tr></thead><tbody class="results"></tbody></table></div>');
            if (rows.length > 0) {
                $('#' + id + ' tbody').append(rows);
            } else {
                $('#' + id + ' tbody').append('<tr><td colspan="'+vars.length||1+'"><em>None</em></td></tr>');
            }
        } else {
            id = insert_into;

            textarea = '<textarea id="'+id+'_querytxt" class="querytxt" style="width:80%; height: 40px;border:1px solid #f0f0f0">'+query_str+'</textarea> <a id="'+id+'_querybtn">+</a>'; // # !!
            if ($('#' + id + ' tbody').length == 0) {
                $('#' + id + ' .result_container').html('<table class="resulttable"><thead><tr><th colspan='+vars.length+'>'+textarea+'</th></tr><tr><th>'+vars.join('</th><th>')+'</th></tr></thead><tbody class="results"></tbody></table>');
            }
            if (rows.length > 0) {
                $('#' + id + ' tbody').append(rows);
            } else {
                $('#' + id + ' tbody').append('<tr><td colspan="'+vars.length+'"><em>None</em></td></tr>');
            }

            $('#' + id + '_querybtn').button();
            $('#' + id + '_querybtn').click(function () {
                window.location.hash = $('#'+id+'_querytxt').text() ;
            });


            $('#' + id + ' .morebtn').remove();
        }

        // Check if there are more results
        if (data.results.bindings.length >= force_result_limit) {
            // User has not provided a limit and we got full results for our own limit
            // Encode and create link
            $('#' + id).append('<a href="#" class="morebtn">More...</a>');
            $('#' + id + ' .morebtn').button();
            $('#' + id + ' .morebtn').click(function () {
                query_str = limit_query(query_str, force_result_limit);
                requery(user_query, query_str, id);
                return false;
            });
        }
    }

    function limit_query(query, offset) {
        // Check if user has given a limit...
        limit_match = query.match(limit_regex);
        if (!limit_match) {
            query = query + ' LIMIT ' + force_result_limit;
        } else if (parseInt(limit_match[2]) > force_result_limit) {
            query = query.replace(limit_regex, "$1" + force_result_limit + "$3");
            final_offset = force_result_limit;
        }
        if (offset) {
            // ... and an offset
            offset_match = query.match(offset_regex);
            if (!offset_match) {
                query = query + ' OFFSET ' + offset;
            } else {
                offset_value = parseInt(offset_match[2]) + offset
                query = query.replace(offset_regex, "$1" + offset_value + "$3");
            }
        }
        return query;
    }

    function do_query(user_query, query_str, id) {
        document.title = title_prefix + ': ' + user_query;
        $('.spo_results').hide();
        $('.result_container').empty();
        $('.query_results').show();
        if (user_query) {
            if (!query_str) {
                query_str = limit_query(user_query)
            }
            $('#'+id+' .result_container').html('<img src="'+deniz_root+'/lib/ajax-loader.gif" alt="loading"/>');
            $.ajax({
                type : 'GET',
                dataType : 'json',
                url : sparql_endpoint,
                data: $.param({'query' : query_str}),
                error: function(req, st, err) { console.log(err); },
                success: function(data, textStatus, xhr) {
                    load_table(data, user_query, query_str, 'query_results');

                    try {
                        editor.setCode(query_str);
                    } catch (e) {
                        console.log("failed to setcode: " + query_str)
                    }
                }
            });
        }
    }

    function save_query(user_query, query_str, query_name, id) {
        if (user_query) {
            if (!query_str) {
                query_str = limit_query(user_query)
            }
            if (!query_name) {
                query_name = prompt("query name") // !
            }
            tp = $('#'+id+' .result_container').innerHTML;
            $('#'+id+' .result_container').html('<img src="'+deniz_root+'/lib/ajax-loader.gif" alt="saving"/>');

            savequery=('INSERT DATA {  <http://'+localapp+'/SavedQueries>'+
                    'rdfs:label "'+query_name+'";'+
                    '_local:sparqlquery "'+query_str+'"'+
                    '}')
            $.ajax({
                type : 'POST',
                dataType : 'json',
                url : sparql_endpoint,
                data: $.param({'query' : query_str, 'name': query_name}),
                error: function(req, st, err) {
                    console.log(err); // !
                    //$('#'+id+' .result_container').empty();
                },
                success: function(data, textStatus, xhr) {
                    alert("saved query: " + query_name);
                    //$('#'id+' .result_container').empty();
                }
            });
   
        }
    }

    function requery(user_query, query_str, id) {
        $.ajax({
            type : 'GET',
            dataType : 'json',
            url : sparql_endpoint,
            data: $.param({'query' : query_str}),
            //error: function(req, st, err) { console.log(err); },
            success: function(data, textStatus, xhr) {
                load_table(data, user_query, query_str, id);
            }
        });
    }

    function fill_spo(query, id) {
        $.ajax({
            type : 'GET',
            dataType : 'json',
            url : sparql_endpoint,
            data: $.param({'query' : query['query']}),
            //error: function(req, st, err) { console.log(err); },
            success: function(data, textStatus, xhr) {
                // Mark-up rows
                var data_trs = [];
                vars = data.head.vars;
                query_str=query['query'];

                load_table(data, query_str, query_str, id);

            }
        });
    }

    function do_spo(iri) {
        document.title = title_prefix + ': ' + iri;
        $('.query_results').hide();
        $('.result_container').empty();
        $('.spo_results').show();
        $('.spo_results .result_container').html('<img src="'+deniz_root+'/lib/ajax-loader.gif" alt="loading"/>');

        /// TODO:?
        $.each({'subject_results': {
                    'a': 'SPARQLQuery',
                    'labelHTML': 'As <strong>Subject</strong>',
                    'query': 'SELECT ?g ?p ?o WHERE { GRAPH ?g { ' + iri + ' ?p ?o } } ORDER BY ?g ?p LIMIT ' + force_result_limit,
                    },
                'predicate_results': {
                    'labelHTML': 'As <strong>Predicate</strong>',
                    'query': 'SELECT ?s ?o WHERE { ?s ' + iri + ' ?o } ORDER BY ?s LIMIT ' + force_result_limit,
                    },
                'object_results': {
                    'labelHTML': 'As <strong>Object</strong>',
                    'query': 'CONSTRUCT { ?s ?p '+ iri +'} WHERE { ?s ?p ' + iri + ' } ORDER BY ?s LIMIT ' + force_result_limit,
                    },
                //todo: lazy/optional
                'type_results': {
                    'labelHTML': 'As <strong>Type</strong>',
                    'query': 'CONSTRUCT { ?s a ' + iri + ' } WHERE { ?s a ' + iri + ' } LIMIT ' + force_result_limit,
                    },
                'graph_results': {
                    'labelHTML': 'As <strong>Graph</strong>',
                    'query': 'SELECT DISTINCT ?s ?p ?o WHERE { GRAPH '+ iri +' { ?s ?p ?o } } ORDER BY ?s ?p LIMIT '+ force_result_limit,
                    },
                },
               function(id, query) {
                   fill_spo(query, id);
                   });
        try {
            editor.setCode(iri);
        } catch(e) { console.log("setcode " + iri + " failed") }
    }

    /* Page load triggered by forward/backward user action or linking to a hashed page */
    function load_page(hash) {
        if (hash == '' || hash == '#') {
            $('.spo_results').hide();
            $('.result_container').empty();
            $('.query_results').hide();
            $('#browsingmenu').show();

            load_browsingmenu();
            document.title = title_prefix;
        } else {
            $('#browsingmenu').hide();
            if (/^</.test(hash)) {
                do_spo(hash);
            } else {
                do_query(hash);
            }
        }
    }

    function load_browsingmenu() {
        // Query named graphs
        $('#browsebygraphs .result_container').html('<img src="'+deniz_root+'/lib/ajax-loader.gif" alt="loading"/>');
        $.ajax({
            type : 'GET',
            dataType : 'json',
            url : sparql_endpoint,
            data: $.param({'query' : "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } ORDER BY ?g LIMIT 10"}),
            //error: function(req, st, err) { console.log(err); },
            success: function(data, textStatus, xhr) {
                lis = ['<li><em><a href="#SELECT ?s ?p ?o WHERE { ?s ?p ?o }">Default graph</a></em></li>'];
                $.each(data.results.bindings, function(i, row) {
                    lis.push('<li><a href="#SELECT ?s ?p ?o WHERE { GRAPH &lt;' + row['g'].value + '&gt; { ?s ?p ?o } } ORDER BY ?s ?p">' + row['g'].value + '</a></li>');
                });
                $('#browsebygraphs .result_container').empty();
                $('#browsebygraphs .result_container').append('<ul>' + lis.join('') + '</ul>');
                // More button
                $('#browsebygraphs .result_container').append('<a href="#" class="morebtn">More...</a>');
                $('#browsebygraphs .result_container .morebtn').button();
                $('#browsebygraphs .result_container .morebtn').click(function () {
                    window.location.hash = "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }";
                    return false;
                });
            }
        });

        // Query concepts
        $('#browsebyconcepts .result_container').html('<img src="'+deniz_root+'/lib/ajax-loader.gif" alt="loading"/>');
        $.ajax({
            type : 'GET',
            dataType : 'json',
            url : sparql_endpoint,
            data: $.param({'query' : "SELECT DISTINCT ?c WHERE { ?s a ?c } LIMIT 6"}),
            //error: function(req, st, err) { console.log(err); },
            success: function(data, textStatus, xhr) {
                lis = [];
                $.each(data.results.bindings, function(i, row) {
                    lis.push('<li>' + render_term(row['c']) + '</li>');
                });
                $('#browsebyconcepts .result_container').empty();
                $('#browsebyconcepts .result_container').append('<ul>' + lis.join('') + '</ul>');
                // More button
                $('#browsebyconcepts .result_container').append('<a href="#" class="morebtn">More...</a>');
                $('#browsebyconcepts .result_container .morebtn').button();
                $('#browsebyconcepts .result_container .morebtn').click(function () {
                    window.location.hash = "SELECT DISTINCT ?c WHERE { ?s a ?c }";
                    return false;
                });
            }
        });
    }

    function update_sparql_endpoint() {
        $('#endpoint-ajax-loader').show();
        // reset css
        $('#endpointoption input').css("background-color", "");

        endpoint = $('#endpointoption input').val();
        $.ajax({
            url: endpoint,
            data: $.param({'query' : "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 1"}),
            //data: $.param({'query' : "ASK {?s ?p ?o}"}), // Use SELECT should be supported by all back-ends
            success: function(data, textStatus, xhr) {
                if (data) {
                    $('#endpoint-ajax-loader').hide();
                    sparql_endpoint = endpoint;
                    $.cookie('deniz_endpoint', sparql_endpoint);
                    $('#endpointoption input').hide();
                    $('#endpointoption .optionvalue span').html(sparql_endpoint);
                    $('#endpointoption .optionvalue').show();
                } else {
                    $('#endpoint-ajax-loader').hide();
                    $('#endpointoption input').css("background-color", "red");
                }
            },
            error: function(req, st, err) {
                $('#endpoint-ajax-loader').hide();
                $('#endpointoption input').css("background-color", "red");
            }
        });
    }

    $(function() {
        // Set sparql endpoint
        endpoint = $.cookie('deniz_endpoint');
        if (endpoint) {
            sparql_endpoint = endpoint;
        }

        $.history.init(load_page);
        $('#executebtn').button();
        $('#executebtn').click(function() {
            window.location.hash = editor.getCode().replace(/\n/g, ' ');
            return false;
        });
        $('#query').resizable({ alsoResize: '.CodeMirror-wrapping' });

        // Show normal text by default and switch to form on click
        $('#endpointoption .optionvalue span').html(sparql_endpoint);
        $('#endpointoption .optionvalue').click(function() {
            $('#endpointoption input').val(sparql_endpoint);
            $('#endpointoption .optionvalue').hide();
            $('#endpointoption input').show();
            $('#endpointoption input').focus();
        });
        $('#endpointoption input').change(update_sparql_endpoint);
        $('#endpointoption input').blur(function() {
            if (sparql_endpoint == $('#endpointoption input').val()) {
                $('#endpointoption .optionvalue').show();
                $('#endpointoption input').hide();
            }
        });
        $('#sparqloptionsform').submit(function() {
            return false;
        });
    });
//]]>

