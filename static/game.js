
// our connection
var ws;
var state;
var actions;

function new_game() {
    if(ws==undefined) {
        ws = new WebSocket("ws://" + document.domain + ':' + location.port + "/ws")
        ws.onopen = function () {
            $('#nav_status').text('connected');
            send_event('start_game', {});
        }
        ws.onclose = function () {
            $('#nav_status').text('Not connected');
            ws = undefined;
            state = undefined;
            actions = undefined;
        }
        ws.onmessage = function (ev) {
            process_event(ev);
        }
    } else {
        send_event('start_game', {});
    }
}

function send_event(event, data) {
    //$('div.message_holder').append(`<div><b style="color: #ac2222">${event}: ${JSON.stringify(data)}</b></div>`)
    console.debug("sent:", event, data);
    ws.send(JSON.stringify([event, data]));
}

function process_event(ev) {
    var data = JSON.parse(ev.data);
    var name = data[0]
    data = data[1]
    console.debug("WebSocket event:", name, data);
    switch (name) {
        case 'game_state':
            //$('div.message_holder').append('<div><b style="color: #ac2222">game_state:' + JSON.stringify(data) + '</div>');
            state = data;
            draw_game(data);
            break;
        case 'status':
            $('h3').remove();
            //$('div.message_holder').append('<div><b style="color: #000">status:' + data + '</div>');
            break;
        case 'choose_action':
            actions = data;
            $('div.message_holder').append('<div><b style="color: #000">choose_action:' + JSON.stringify(data) + '</div>');
            $('div.actions').empty();
            for (const [key, value] of Object.entries(data)) {
                $('div.actions').append('<button onclick=send_action(' + key + ')>' + value + '<button/>');
            }
            if(state.player.hand.length > 0) {
                $('div.actions').append('<button onclick=send_action("all")>play all<button/>');
            }
            draw_game(state);
            break;
         case 'choose_piles':
            //$('div.message_holder').append('<div><b style="color: #000">choose_piles:' + JSON.stringify(data) + '</div>');
            $('div.actions').empty();
            choose_piles(data, function (pile, cards) {
                var card_names = cards;
                send_event('choose_piles', {'pile': pile, 'cards': card_names});
            });
            break;
         case 'player_won':
            state = data;
            draw_game(data);
            game_over('we won!')
            break;
         case 'player_lost':
            state = data;
            draw_game(data);
            game_over('you lost :(')
            break;
    }
}

function game_over(msg) {
    $('#game_over_status').html(msg);
    $('#game_over').show();
}

function hide_and_new_game() {
    $('#game_over').hide();
    new_game();
}

function send_action(a) {
    send_event('choose_action', {'action': a});
}

function draw_game(state) {
    var trade = state['player']['trade'];

    var trade_pile = $('#trade-row > ul');
    trade_pile.empty();
    trade_pile.append(draw_buyable_card('Explorer'))
    for (const card of state['trade_pile']) {
        trade_pile.append(draw_buyable_card(card))
    }
    draw_player(state['player']);
    draw_other_player(state['other_player']);
}

function draw_player(p) {
    var bases = p['bases'].map(draw_base);
    bases = bases.concat(p['outposts'].map(draw_base));
    $('div#bases_me > ul').html(bases.join(""));

    var inplay= p['in_play'].map(draw_card);
    $('div#inplay > ul').html(inplay.join(""));

    var hand= p['hand'].map(draw_playable_card);
    $('div#hand > ul').html(hand.join(""));

    draw_player_stats(p, $('div#player_me'));
}

function draw_other_player(p) {
    var bases = p['bases'].map(draw_card);
    bases = bases.concat(p['outposts'].map(draw_card));
    $('div#bases_other > ul').html(bases.join(""));
    draw_player_stats(p, $('div#player_other'));
}

function draw_player_stats(p, ele) {
    var info = [];
    info.push(`<div>HP: ${p['health']}</div>`);
    info.push(`<div>TRADE: ${p['trade']}</div>`);
    info.push(`<div>DMG: ${p['damage']}</div>`);
    info.push(`<div>DISCARD: ${p['discard']}</div>`);
    ele.html(info.join(""));
}

function draw_card(card) {
    var name;
    if(typeof card == "string") {
        name = card;
    } else {
        name = card['name'];
    }
    return `<li class='card-row' name="${name}"><img src="/card/${name}" alt="${name}"></img></li>`;
}

function draw_base(card) {
    var name;
    if(typeof card == "string") {
        name = card;
    } else {
        name = card['name'];
    }
    return `<li class='card-col'><img src="/base/${name}" alt="${name}"></img></li>`;
}

function draw_buyable_card(card) {
    var name;
    if(typeof card == "string") {
        name = card;
    } else {
        name = card['name'];
    }
    var action = get_action("buy " + name);

    if(action) {
        return `<li class='card-row buyable'><img src="/card/${name}" onclick='send_action("${action}")' alt="${name}"></img></li>`;
    } else {
        return `<li class='card-row notbuyable'><img src="/card/${name}" alt="${name}"></img></li>`;
    }
}

function get_action(action_name) {
    if (actions) {
        for (const [key, value] of Object.entries(actions)) {
            if (value == action_name)
                return key;
        }
    }
}

function draw_playable_card(card) {
    var name = card['name'];
    var action = get_action("play " + name);
    if (action) {
        return `<li class='card-row'><img src="/card/${name}" onclick='send_action("${action}")' alt="${name}"></img></li>`;
    } else {
        return `<li class='card-row'><img src="/card/${name}" alt="${name}"></img></li>`;
    }
}

function choose_piles(data, callback) {
    const min_select = data.min;
    const max_select = data.max;
    var num_selected = 0;
    var pile_selected = undefined;

    var html = [];
    html.push(`<h2>${data['action']} <span id="num">0</span>/${data['min']}-${data['max']}</h2>`);
    html.push(`<button id="choose_piles_done">done</button>`)
    for (const pile of data['piles']) {
        let card_pile;
        if (pile == 'trade_pile') {
            card_pile = state.trade_pile;
        } else {
            card_pile = state.player[pile];
        }
        console.assert(card_pile, {"pile": pile});
        if (card_pile.length >= min_select) {
            var cards = card_pile.map(draw_card).join("");
            html.push(`<div><h3>${pile}</h3><ul class="card-list" pile="${pile}">${cards}</ul></div>`);
        }
    }

    const modal = $("#choose_cards");
    modal.html(html.join(""));

    const selectable_cards = modal.find(".card-row");
    // selection/unselection logic
    for(const c of selectable_cards) {
        c.addEventListener("click", function () {
            if(this.classList.contains("selected")) {
                // unselect
                this.classList.remove("selected");
                num_selected -= 1;
            } else if(num_selected < max_select) {
                this.classList.add("selected");
                pile_selected = this.parentElement.attributes.pile.value;
                num_selected += 1;
            }
            update_status();
        });
    }
    function update_status() {
        //console.log("in update_status");
        if(num_selected>=min_select) {
            $("#choose_piles_done").visibility = "visible";
        } else {
            $("#choose_piles_done").visibility = "hidden";
        }
        if(pile_selected != undefined) {
            const selected = modal.find(`ul[pile=${pile_selected}] > .selected`);
            num_selected = selected.length;
            modal.find("#num").text(num_selected);
        }
    }

    // done with selection!
    $("#choose_piles_done").click(function () {
        var card_names = [];
        if(pile_selected != undefined) {
            const selected = modal.find(`ul[pile=${pile_selected}] > .selected`);
            card_names = selected.toArray().map(li=>li.attributes.name.value);
        }
        modal.empty();
        modal.hide();
        callback(pile_selected, card_names);
    });

    update_status();
    modal.show();
}

function test_choose_piles() {
    choose_piles({"action":"test", "min":1, "max":2, "piles":["hand","discard_pile"]}, console.info);
}
