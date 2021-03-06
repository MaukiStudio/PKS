'use strict';

angular.module('placeApp', [])
.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');
})
.controller('blogSearchCtrl', ['$scope', '$q', '$http', function($scope, $q, $http){
  function makeKeyword() {
    var keyword = '';
    var placeName = ($('#place-name')[0] !== undefined) ? $('#place-name')[0].innerHTML : '';
    var placeAddr = ($('#place-addr')[0] !== undefined) ? $('#place-addr')[0].innerHTML : '';

    if (placeAddr && placeAddr !== '') {
      var region_items = placeAddr.split(' ');
      var loopCount = region_items.length >= 4 ? 4 : region_items.length;
      for (var i = 1; i < loopCount; i++) {
        keyword += region_items[i] + '+';
      }

      keyword += placeName;
      console.log('Calculated keyword : ', keyword);
      keyword = encodeURI(keyword);
      console.log('URL encoded keyword : ', keyword);
    }
    return keyword;
  };

  function search(keyword) {
    var deferred = $q.defer();

    $http({
      method: 'JSONP',
      url: 'https://apis.daum.net/search/blog?apikey=f4e2c3f6c532baf54ec80e81f08fc1a1&callback=JSON_CALLBACK&q=' + keyword + '&output=json'
    })
    .then(function(response) {
      // console.dir(response.data);
      deferred.resolve(response.data.channel.item);
    }, function(err) {
      console.error(err);
      deferred.reject(err);
    });

    return deferred.promise;
  }

  function getDaumResult() {
    var keyword = makeKeyword();
    if (keyword !== '') {
      search(keyword)
      .then(function(items) {
        $scope.searchResults = [];
        for (var i = 0; i < items.length / 2; i++) {
          items[i].title = items[i].title.replace(/<b>/g, '').replace(/&lt;b&gt;/g, '').replace(/&lt;\/b&gt;/g, '').replace(/&quot;/g, '"');
          items[i].description = items[i].description.replace(/<b>/g, '').replace(/&lt;b&gt;/g, '').replace(/&lt;\/b&gt;/g, '').replace(/&quot;/g, '"');
          items[i].description = items[i].description.substr(0, items[i].description.length/2) + '...';
          $scope.searchResults.push(items[i]);
        }

        // console.dir($scope.searchResults);

      }, function(err) {
        $scope.searchResults = [];
        $scope.searchResults.push({
          author: 'MAUKI studio',
          comment: '',
          description: JSON.stringify(err),
          link: '',
          title: '검색 결과를 얻어 오는데 실패했습니다'
        })
      });
    }
  };

  getDaumResult();
}]);
