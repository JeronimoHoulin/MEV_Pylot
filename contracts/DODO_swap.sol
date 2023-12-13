/*
    Copyright 2021 DODO ZOO.
    SPDX-License-Identifier: Apache-2.0
*/
pragma solidity ^0.8;
pragma abicoder v2;
//ERC-20
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
//ONE INCH
import "@openzeppelin/contracts/access/Ownable.sol";
//UNISWAP
import "@uniswap/v3-periphery/contracts/libraries/TransferHelper.sol";
import "@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol";

interface IDODO {
    function flashLoan(
        uint256 baseAmount,
        uint256 quoteAmount,
        address assetTo,
        bytes calldata data
    ) external;

    function _BASE_TOKEN_() external view returns (address);
    function _BASE_RESERVE_() external view returns (uint112);
    function _QUOTE_TOKEN_() external view returns (address);
    function _QUOTE_RESERVE_() external view returns (uint112);
}


contract DODOFlashArbi is Ownable{

    //1inch
    struct SwapDescription {
        IERC20 srcToken;
        IERC20 dstToken;
        address srcReceiver;
        address dstReceiver;
        uint256 amount;
        uint256 minReturnAmount;
        uint256 flags;
        bytes permit;
    }

    //Uni
    ISwapRouter public constant swapRouter =
        ISwapRouter(0xE592427A0AEce92De3Edee1F18E0157C05861564);

    //OneINch router
    //0x1111111254EEB25477B68fb85Ed929f73A960582 (for deployment)

    //1inch
    address immutable AGGREGATION_ROUTER_V5;
    //Security
    address immutable initial_owner;
    
    constructor(address oneinchrouter, address initialOwner) Ownable(initialOwner) {
        AGGREGATION_ROUTER_V5 = oneinchrouter;
        initial_owner = initial_owner;
    }




    //Note: CallBack function executed by DODOV2(DVM) flashLoan pool
    function DVMFlashLoanCall(
        address sender,
        uint256 baseAmount,
        uint256 quoteAmount,
        bytes calldata data
    ) external {
        _flashLoanCallBack(sender, baseAmount, quoteAmount, data);
    }

    //Note: CallBack function executed by DODOV2(DPP) flashLoan pool
    function DPPFlashLoanCall(
        address sender,
        uint256 baseAmount,
        uint256 quoteAmount,
        bytes calldata data
    ) external {
        _flashLoanCallBack(sender, baseAmount, quoteAmount, data);
    }

    //Note: CallBack function executed by DODOV2(DSP) flashLoan pool
    function DSPFlashLoanCall(
        address sender,
        uint256 baseAmount,
        uint256 quoteAmount,
        bytes calldata data
    ) external {
        _flashLoanCallBack(sender, baseAmount, quoteAmount, data);
    }



    ///////// DODO LOAN

    function dodoFlashLoan(
        address flashLoanPool, //You will take a loan from this DODOV2 pool
        uint256 loanAmount,
        address loanToken,
        uint minOutOneInch, 
        bytes calldata _dataOneInch
    ) external {
        //Note: The data can be structured with any variables required by your logic. The following code is just an example
        address flashLoanBase = IDODO(flashLoanPool)._BASE_TOKEN_();

        if (flashLoanBase == loanToken) {
            address through_token = IDODO(flashLoanPool)._QUOTE_TOKEN_();
            bytes memory data = abi.encode(flashLoanPool, loanToken, through_token, loanAmount, minOutOneInch, _dataOneInch);
            IDODO(flashLoanPool).flashLoan(loanAmount, 0, address(this), data);
        } else {
            address through_token = flashLoanBase;
            bytes memory data = abi.encode(flashLoanPool, loanToken, through_token, loanAmount, minOutOneInch, _dataOneInch);
            IDODO(flashLoanPool).flashLoan(0, loanAmount, address(this), data);
        }
    }


    /////////UNISWAP SWAP
    // ADDED DIRECTLY IN THE CALLBACK.


    /////////ONEINCH SWAP

    function oneInchSwap(uint minOut, SwapDescription memory desc, bytes memory _d) private returns (uint retAmount) {
        //(address _c, SwapDescription memory desc, bytes memory _d) = abi.decode(_data[4:], (address, SwapDescription, bytes));

        //IERC20(desc.srcToken).transferFrom(msg.sender, address(this), desc.amount);  I don't need this as the fund's will come form the FLash Loan.
        IERC20(desc.srcToken).approve(AGGREGATION_ROUTER_V5, desc.amount);

        (bool succ, bytes memory responseData) = address(AGGREGATION_ROUTER_V5).call(_d);
        if (succ) {
            (uint returnAmount, uint gasLeft) = abi.decode(responseData, (uint, uint));
            require(returnAmount >= minOut);
            return returnAmount;
        } else {
            revert("Swap failed");
        }
    }









    /////////////////////////////////////// HANDLE LOGIC IN LOAN CALLBACK

    function _flashLoanCallBack(
        address sender,
        uint256,
        uint256,
        bytes memory data
    ) internal {
        (address flashLoanPool, address loanToken, address throughToken, uint256 loanAmount, uint minOutOneInch, bytes memory _dataOneInch) = abi
            .decode(data, (address, address, address, uint256, uint, bytes));

        require(
            sender == address(this) && msg.sender == flashLoanPool,
            "HANDLE_FLASH_DENIED"
        );

        // Note: Realize your own logic using the token from flashLoan pool.
        require(
            loanAmount == IERC20(loanToken).balanceOf(address(this)),
            "The loanAmount and the current balance should be the same!"
        );

        if (loanAmount > 0) {

            // ARBITRAGE LOGIC:

            // ONE INCH SWAP:
            require(_dataOneInch.length >= 4, "Invalid _dataOneInch length");
            uint dataLength;
            assembly {
                dataLength := mload(add(_dataOneInch, 0x20))
            }
            require(_dataOneInch.length >= dataLength + 4, "Invalid _dataOneInch data");
            bytes memory slicedData = new bytes(dataLength);
            assembly {
                mstore(add(slicedData, 0x20), add(add(_dataOneInch, 0x24), dataLength))
            }
            (address _c, SwapDescription memory desc, bytes memory _d) = abi.decode(slicedData, (address, SwapDescription, bytes));

            uint oneInchReturnAmount = oneInchSwap(minOutOneInch, desc, _d);





            // UNISWAP SWAP

            //TransferHelper.safeTransferFrom(tokenIn, msg.sender, address(this), oneInchReturnAmount); SC WILL HAVE THE TOKENS.
            TransferHelper.safeApprove(throughToken, address(swapRouter), oneInchReturnAmount);

            ISwapRouter.ExactInputSingleParams memory params = ISwapRouter
                .ExactInputSingleParams({
                    tokenIn: throughToken,
                    tokenOut: loanToken,
                    fee: 500, // pool fee 0.05%
                    recipient: address(this), //SC... NOT msg.sender
                    deadline: block.timestamp,
                    amountIn: oneInchReturnAmount,
                    amountOutMinimum: loanAmount,
                    sqrtPriceLimitX96: 0
                });

            uint amountOut = swapRouter.exactInputSingle(params);

            require(amountOut > loanAmount); //PROFIT MADE


            

            // Return loaned funds to DODO.
            IERC20(loanToken).transfer(flashLoanPool, amountOut);

            // Return profit to MSG.SENDER.
            uint profit = IERC20(loanToken).balanceOf(address(this));
            IERC20(loanToken).transfer(msg.sender, profit);
        }
    }
}