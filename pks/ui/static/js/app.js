'use strict';

angular.module('placeApp', [])
.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');
})
.controller('blogSearchCtrl', ['$scope', '$q', 'daumSearchService', function($scope, $q, daumSearchService){
  function makeKeyword() {
    var keyword = '리우올림픽';
    // if ($scope.post.placePost) {
    //   var region = $scope.post.placePost.addr2 || $scope.post.placePost.addr1 || $scope.post.placePost.addr3 || null;
    //   if (region) {
    //     var region_items = region.content.split(' ');
    //     var loopCount = region_items.length >= 4 ? 4 : region_items.length;
    //     for (var i = 1; i < loopCount; i++) {
    //       keyword += region_items[i] + '+';
    //     }
    //   }
    //
    //   keyword += ($scope.post.placePost.name.content || $scope.post.userPost.name.content);
    //   console.log('Calculated keyword : ', keyword);
    //   keyword = encodeURI(keyword);
    //   console.log('URL encoded keyword : ', keyword);
    // }
    return keyword;
  };

  function search(keyword) {
    var deferred = $q.defer();

    $http({
      method: 'GET',
      url: 'https://apis.daum.net/search/blog?apikey=f4e2c3f6c532baf54ec80e81f08fc1a1&q=' + keyword + '&output=json'
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
        $scope.searchResults = items;
        for (var i = 0; i < $scope.searchResults.length; i++) {
          $scope.searchResults[i].title = $scope.searchResults[i].title.replace(/<b>/g, '').replace(/&lt;b&gt;/g, '').replace(/&lt;\/b&gt;/g, '').replace(/&quot;/g, '"');
          $scope.searchResults[i].description = $scope.searchResults[i].description.replace(/<b>/g, '').replace(/&lt;b&gt;/g, '').replace(/&lt;\/b&gt;/g, '').replace(/&quot;/g, '"');
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
