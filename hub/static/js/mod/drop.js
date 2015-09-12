define('mod/drop', [
    'jquery'
], function($){
  $(document).ready(function(){
    // var dropzone = document.getElementById("dropzone");
    var dropzone = document.body, 
        count = 0;
    // 拖拽元素进入目标区域
    dropzone.addEventListener('dragenter', dragEnterHandler);
    // 拖拽元素在目标区域移动
    dropzone.addEventListener('dragover', dragOverHandler);
    // 拖拽元素离开目标区域
    dropzone.addEventListener('dragleave', dragLeaveHandler);
    // 将拖拽元素放在目标区域
    dropzone.addEventListener('drop', dropHandler);

    function dragEnterHandler(e){
      e.stopPropagation();
      e.preventDefault();
      $('#dropzone').show();
      if(count<1) count = 0;
      count++;
    }

    function dragOverHandler(e){
      e.stopPropagation();
      e.preventDefault();
    }

    function dragLeaveHandler(e){
      e.stopPropagation();
      e.preventDefault();
      count--;
      if(count<1){
        $('#dropzone').hide();
        count = 0;
      }
    }

    function dropHandler(e){
      e.stopPropagation();
      e.preventDefault();

      var fileList = e.dataTransfer.files,
          fileNum = fileList.length;

      if (fileNum === 0) return;
      file = fileList[0];
      for(var i=0; i<fileNum; i++) actFile(fileList[i]);

      $('#dropzone').hide();
      count = 0;
    }

    function actFile(f){
      // is image? ignore
      if (f.type.indexOf('image') > -1) return;

      var _reader = new FileReader(),
          _name = f.name;
      _reader.onload = (function(f) {
        return function(e){
          var _edr = getEmptyEditor(),
              _index = editors.indexOf(_edr),
              _nameInput = $('input[name="gist_name"]')[_index];
          $(_nameInput).val(_name).change();
          _edr.setOption('value', e.target.result);
        } 
      })(f);
      _reader.readAsText(f);
    }

    function getEmptyEditor(){
      var _edr;
      for(var i=0; i<editors.length; i++){
        var _name = $($('input[name="gist_name"]')[i]).val(),
            _cont = editors[0].getValue();
        if(_name==''&&_cont==''){
          _edr = editors[i];
          break;
        }
      }
      if(!_edr){
        $('.js-add-gist-file').click();
        _edr = editors[editors.length-1];
      }
      return _edr;
    }

  });
});
