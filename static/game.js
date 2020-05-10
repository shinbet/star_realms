
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
            $('div.message_holder').append('<div><b style="color: #000">status:' + data + '</div>');
            break;
        case 'choose_action':
            actions = data;
            $('div.message_holder').append('<div><b style="color: #000">choose_action:' + JSON.stringify(data) + '</div>');
            $('div.actions').empty();
            for (const [key, value] of Object.entries(data)) {
                $('div.actions').append('<button onclick=send_action(' + key + ')>' + value + '<button/>');
            }
            draw_game(state);
            break;
         case 'choose_piles':
            $('div.message_holder').append('<div><b style="color: #000">choose_piles:' + JSON.stringify(data) + '</div>');
            $('div.actions').empty();

            break;
    }
}

function send_action(a) {
    send_event('choose_action', {'action': a});
}

function draw_game(state) {
    var trade = state['player']['trade'];

    var trade_pile = $('#trade-row');
    trade_pile.empty();
    trade_pile.append(draw_buyable_card('Explorer'))
    for (const card of state['trade_pile']) {
        trade_pile.append(draw_buyable_card(card))
    }
    draw_player(state['player']);
    draw_other_player(state['other_player']);
}

function draw_player(p) {
    var bases = p['bases'].map(draw_card);
    bases = bases.concat(p['outposts'].map(draw_card));
    $('div#bases_me').html(bases.join(""));

    var inplay= p['in_play'].map(draw_card);
    $('div#inplay').html(inplay.join(""));

    var hand= p['hand'].map(draw_playable_card);
    $('div#hand').html(hand.join(""));

    draw_player_stats(p, $('div#player_me'));
}

function draw_other_player(p) {
    var bases = p['bases'].map(draw_card);
    bases = bases.concat(p['outposts'].map(draw_card));
    $('div#bases_other').html(bases.join(""));
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
    return `<div class='card-col'><img src="/card/${name}" alt="${name}"></img></div>`;
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
        return `<div class='card-col buyable'><img src="/card/${name}" onclick='send_action("${action}")' alt="${name}"></img></div>`;
    } else {
        return `<div class='card-col notbuyable'><img src="/card/${name}" alt="${name}"></img></div>`;
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
        return `<div class='card-col'><img src="/card/${name}" onclick='send_action("${action}")' alt="${name}"></img></div>`;
    } else {
        return `<div class='card-col'><img src="/card/${name}" alt="${name}"></img></div>`;
    }
}
