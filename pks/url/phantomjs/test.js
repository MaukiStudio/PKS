var page = require('webpage').create();

var system = require('system');

var fs = require('fs');


if (system.args.length === 1){

    console.log('Usage: test.js <some URL>');

    phantom.exit();

}


var address = system.args[1];

page.open(address, function(status){

     if (status) {

         fs.write('test.html', page.content, 'w');

     }

     phantom.exit();

});
