'use strict';

goog.provide('Blockly.JSON');

/**
 * Encode a block tree as JSON.
 * @param {!Object} workspace The SVG workspace.
 * @return {!Element} JSON object.
 */
Blockly.JSON.workspaceToJson = function(workspace) {
  var blocks = workspace.getTopBlocks(true);
  if (blocks[0]) {
    var json = Blockly.JSON.blockToJson(blocks[0]);
  }
  return JSON.stringify(json);
};

/**
 * Encode a block subtree as JSON.
 * @param {!Blockly.Block} block The root block to encode.
 * @return {!Element} Tree of JSON object.
 * @private
 */
Blockly.JSON.blockToJson = function(block) {
  var element = {};
  element['type'] = block.type;
  element['id'] = block.id;
  for (var x = 0, input; input = block.inputList[x]; x++) {
    for (var y = 0, field; field = input.fieldRow[y]; y++) {
      if (field.name && field.EDITABLE) {
        element[field.name] = field.getValue();
      }
    }
  }
  var hasValues = false;
  for (var i = 0, input; input = block.inputList[i]; i++) {
    var empty = true;
    if (input.type == Blockly.DUMMY_INPUT) {
      continue;
    } else {
      var childBlock = input.connection.targetBlock();
      if (childBlock) {
        element[input.name] = Blockly.JSON.blockToJson(childBlock);
      }
    }
  }
  if (hasValues) {
    element['inline'] = block.inputsInline;
  }
  if (block.isCollapsed()) {
    element['collapsed'] = true;
  }
  if (block.disabled) {
    element['disabled'] = true;
  }
  if (!block.isDeletable()) {
    element['deletable'] = false;
  }
  if (!block.isMovable()) {
    element['movable'] = false;
  }
  if (!block.isEditable()) {
    element['editable'] = false;
  }
  if ( block.elseifCount_ ) {
    element['M_elseifCount'] = block.elseifCount_
  }
  if ( block.elseCount_ ) {
    element['M_elseCount'] = block.elseCount_
  }
  if ( block.itemCount_ ) {
    element['M_itemCount'] = block.itemCount_
  }
  var nextBlock = block.getNextBlock();
  if (nextBlock) {
    element['NEXT']= Blockly.JSON.blockToJson(nextBlock);
  }

  return element;
};

/**
 * Decode an JSON Object and create blocks on the workspace.
 * @param {!Blockly.Workspace} workspace The SVG workspace.
 * @param {!Element} JSON.
 */
Blockly.JSON.jsonToWorkspace = function(workspace, json) {
  Blockly.JSON.jsonToBlock(workspace, json);
};

/**
 * Decode an JSON block tag and create a block (and possibly sub blocks) on the
 * workspace.
 * @param {!Blockly.Workspace} workspace The workspace.
 * @param {!Element} JSON block element.
 * @param {boolean=} opt_reuseBlock Optional arg indicating whether to
 *     reinitialize an existing block.
 * @return {!Blockly.Block} The root block created.
 * @private
 */
Blockly.JSON.jsonToBlock = function(workspace, jsonBlock, opt_reuseBlock) {
  var block = null;
  var prototypeName = jsonBlock['type'];
  if (!prototypeName) {
    throw 'Block type unspecified: \n';
  }
  var id = jsonBlock['id'];
  if (opt_reuseBlock && id) {
    block = Blockly.Block.getById(id, workspace);
    if (!block) {
      throw 'Couldn\'t get Block with id: ' + id;
    }
    var parentBlock = block.getParent();
    // If we've already filled this block then we will dispose of it and then
    // re-fill it.
    if (block.workspace) {
      block.dispose(true, false, true);
    }
    block.fill(workspace, prototypeName);
    block.parent_ = parentBlock;
  } else {
    block = workspace.newBlock( prototypeName);
  }
  if (!block.svg_) {
    block.initSvg();
  }

  var inline = jsonBlock['inline'];
  if (inline) {
    block.setInputsInline(inline == 'true');
  }
  var disabled = jsonBlock['disabled'];
  if (disabled) {
    block.setDisabled(disabled == 'true');
  }
  var deletable = jsonBlock['deletable'];
  if (deletable) {
    block.setDeletable(deletable == 'true');
  }
  var movable = jsonBlock['movable'];
  if (movable) {
    block.setMovable(movable == 'true');
  }
  var editable = jsonBlock['editable'];
  if (editable) {
    block.setEditable(editable == 'true');
  }
  var collapsed = jsonBlock['collapsed'];
  if (collapsed) {
    block.setCollapsed(collapsed == 'true');
  }

  // handle mutations
  if ( block.domToMutation) {
      var mut = document.createElement('div');
      if ( jsonBlock['M_elseifCount'] ) {
        mut.setAttribute('elseif', jsonBlock['M_elseifCount'])
      }
      if ( jsonBlock['M_elseCount'] ) {
        mut.setAttribute('else', jsonBlock['M_elseCount'])
      }
      if ( jsonBlock['M_itemCount'] ) {
        mut.setAttribute('items', jsonBlock['M_itemCount'])
      }
      block.domToMutation(mut);
  }

  if(block.afterRender) {
    block.afterRender();
  }

  var blockChild = null;
  for(var key in jsonBlock) {
    if (['id', 'type'].indexOf(key) == -1) {
      var jsonChild = jsonBlock[key];
      if (jsonChild) { // not null
        var input;
        switch (typeof(jsonChild)) {
          case 'string':
          case 'boolean':
              block.setFieldValue(jsonChild, key);
            break;
          case 'object':
            blockChild = Blockly.JSON.jsonToBlock(workspace, jsonChild,
                  opt_reuseBlock);
            if (key == 'NEXT') {
              if (!block.nextConnection) {
                throw 'Next statement does not exist.';
              } else if (block.nextConnection.targetConnection) {
                // This could happen if there is more than one XML 'next' tag.
                throw 'Next statement is already connected.';
              }
              if (!blockChild.previousConnection) {
                throw 'Next block does not have previous statement.';
              }
              block.nextConnection.connect(blockChild.previousConnection);
            } else {
            input = block.getInput(key);
              if (!input) {
                throw 'Input ' + key + ' does not exist in block ' + prototypeName;
              }
              if (blockChild.outputConnection) {
                input.connection.connect(blockChild.outputConnection);
              } else if (blockChild.previousConnection) {
                input.connection.connect(blockChild.previousConnection);
              } else {
                throw 'Child block does not have output or previous statement.';
              }
            }
            break;
          default:
            // Unknown tag; ignore.  Same principle as HTML parsers.
        }
      }
    }
  }

  var next = block.nextConnection && block.nextConnection.targetBlock();
  if (next) {
    next.render();
  } else {
    block.render();
  }
  return block;
};

// Export symbols that would otherwise be renamed by Closure compiler.
Blockly['JSON'] = Blockly.JSON;
Blockly.JSON['jsonToWorkspace'] = Blockly.JSON.jsonToWorkspace;
Blockly.JSON['workspaceToJson'] = Blockly.JSON.workspaceToJson;
